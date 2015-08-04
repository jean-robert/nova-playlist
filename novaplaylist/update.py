# -*- coding: utf-8 -*-

import logging

import datetime
from mutagenerate.core import AmazonSource
import os
import random
import requests_cache
from optparse import OptionParser
from collections import Counter

from scrapers import NovaScraper, FipScraper, OuiScraper, NostalgieScraper, RadioparadiseScraper
from core.tools import os_query, parse_duration, create_directory
from core.youtubeapi import YouTubeAPI


parser = OptionParser()
parser.add_option("", "--lookback", dest="lookback", default="7d", help=u"Période en secondes")
parser.add_option("", "--strategy", dest="strategy", default="mostcommon", help=u"Stratégie parmi (mostcommon, random, mixed)")
parser.add_option("", "--titles", dest="titles", default=20, type="int", help=u"nombre de titres à sélectionner pour la playslist")
parser.add_option("", "--workspace", dest="workspace", default="")
parser.add_option("", "--radio", dest="radio", default="nova")
parser.add_option("", "--youtube-dl-bin", dest="youtube_dl_bin", default="youtube-dl")
parser.add_option("", "--no-upload", dest="no_upload", default=False, action="store_true")
parser.add_option("", "--youtube-id-source", dest="youtube_id_source", default="scrap", help=u"Méthode de récupération des ids YouTube (scrap, search)")
parser.add_option("", "--playlist-id", dest="playlist_id", default=None, help=u"Id de la playlist pour uploader sur un channel YouTube")

options, args = parser.parse_args()

source = AmazonSource()
logger = logging.getLogger('nova-playlist')


def buildPlaylist(songs, title_nb, strategy):
    playlist = Counter(songs).most_common()
    if strategy == "random":
        random.shuffle(playlist)
    elif strategy == "mixed":
        playlist2 = playlist[:(title_nb / 2)]
        playlist3 = filter(lambda title: title not in playlist2, playlist)
        random.shuffle(playlist3)
        playlist = playlist2 + playlist3[:(title_nb / 2)]
    playlist = playlist[:title_nb]
    for i, (song, broadcast_nb) in enumerate(playlist):
        logger.info("#%(i).3d %(song)s %(broadcast_nb)s broadcasts" % locals())
    return [i[0] for i in playlist]


def downloadMP3(youtube_dl_bin, working_directory, songs):
    create_directory(working_directory)
    ok_songs = []
    for s, song in enumerate(songs):
        try:
            song.download(youtube_dl_bin, working_directory)
            song.tag(working_directory, s + 1, source)
            ok_songs.append(song)
        except OSError as e:
            logger.warning("Cannot download %(song)s, %(e)s" % locals())
    return ok_songs


def makePlaylistFile(songs, working_directory):
    with open("%(working_directory)s/nova-playlist.m3u" % locals(), 'w+') as f:
        f.write("\n".join([song.filename(".").encode("utf8") for song in songs]))


def syncDropBox(songs, working_directory):
    current_directory = os.path.dirname(os.path.abspath(__file__))
    os_query("%(current_directory)s/dropbox_uploader.sh delete music" % locals())
    os_query("%(current_directory)s/dropbox_uploader.sh mkdir music" % locals())
    os_query("%(current_directory)s/dropbox_uploader.sh upload %(working_directory)s/nova-playlist.m3u music" % locals())
    for song in songs:
        fn = song.filename(working_directory)
        if os.path.exists(fn):
            os_query("""%(current_directory)s/dropbox_uploader.sh upload "%(fn)s" music""" % locals())


if __name__ == "__main__":
    lookback = parse_duration(options.lookback)
    ts_beg = datetime.datetime.now() - datetime.timedelta(seconds=lookback)
    ts_beg = datetime.datetime(ts_beg.year, ts_beg.month, ts_beg.day, ts_beg.hour)
    ts_end = datetime.datetime.now()

    working_directory = os.path.join(os.getcwd(), "music")
    if options.workspace:
        requests_cache.install_cache(
            cache_name=options.workspace,
            allowable_methods=('GET', 'POST')
        )

    if options.radio == "fip":
        songs = FipScraper().scrap(ts_beg, ts_end)
    elif options.radio == "oui":
        songs = OuiScraper().scrap(ts_beg, ts_end)
    elif options.radio == "nostalgie":
        songs = NostalgieScraper().scrap(ts_beg, ts_end)
    elif options.radio == "radioparadise":
        songs = RadioParadiseScraper().scrap(ts_beg, ts_end)
    else:
        songs = NovaScraper().scrap(ts_beg, ts_end)

    logger.info("Construit la playlist de " + str(options.titles) + " titres")
    songs = buildPlaylist(songs, options.titles, options.strategy)

    logger.info("Récupère les liens YouTube")
    yta = YouTubeAPI()
    for song in songs:
        if options.youtube_id_source == "scrap":
            song.youtube_id = yta.scrap_youtube_id(str(song))
        if options.youtube_id_source == "search":
            song.youtube_id = yta.search_youtube_id(str(song))

    if options.playlist_id:
        logger.info("Clean la playlist actuelle")
        yta.clean_channel_playlist(options.playlist_id)

        logger.info("Construit la nouvelle playlist sur le channel")
        yta.build_channel_playlist(options.playlist_id, songs)

    else:
        logger.info("Clean les anciens et télécharge les nouveaux .mp3")
        songs = downloadMP3(options.youtube_dl_bin, working_directory, songs)

        logger.info("Construit le fichier de playlist")
        makePlaylistFile(songs, working_directory)

        if not options.no_upload:
            syncDropBox(songs, working_directory)

    logger.info("Update terminé !")
