# -*- coding: utf-8 -*-

import logging
from core.logorigins import logger

import datetime
from mutagenerate.core import AmazonSource
import os
import random
import re
import requests
import requests_cache
import urllib
from optparse import OptionParser
from collections import Counter

from scrapers import NovaScraper, FipScraper, OuiScraper, NostalgieScraper
from core.tools import os_query, parse_duration, create_directory


parser = OptionParser()
parser.add_option("", "--log-level", dest="log_level", default="info", help="verbosity : debug, info, warning, error, critical")
parser.add_option("", "--log-filter", dest="log_filter", default="", help="")
parser.add_option("", "--lookback", dest="lookback", default="7d", help=u"Période en secondes")
parser.add_option("", "--strategy", dest="strategy", default="mostcommon", help=u"Stratégie parmi (mostcommon, random, mixed)")
parser.add_option("", "--titles", dest="titles", default=20, type="int", help=u"nombre de titres à sélectionner pour la playslist")
parser.add_option("", "--workspace", dest="workspace", default="")
parser.add_option("", "--radio", dest="radio", default="nova")
parser.add_option("", "--youtube-dl-bin", dest="youtube_dl_bin", default="youtube-dl")
parser.add_option("", "--no-upload", dest="no_upload", default=False, action="store_true")

options, args = parser.parse_args()
default_level = getattr(logging, options.log_level.upper())
for l in logging.Logger.manager.loggerDict.values():
    if isinstance(l, logging.Logger):
        l.setLevel(default_level)
if options.log_filter:
    for logger_name, level in [token.split(":") for token in options.log_filter.split(",")]:
        logging.getLogger(logger_name).setLevel(getattr(logging, level.upper()))


source = AmazonSource()


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


def scrapYouTube(songs):
    retval = []
    for song in songs:
        url = "http://www.youtube.com/results?search_query=%s" % urllib.quote_plus(str(song))
        page = requests.get(url, timeout=15)

        if 'Aucune vid' in page.content:
            logger.warning("No video found for %(song)s" % locals())
            song.youtube_id = None
        else:
            youtube_id = re.findall('href="\/watch\?v=(.*?)[&;"]', page.content)[0]
            logger.info("Found %(youtube_id)s for song %(song)s" % locals())
            song.youtube_id = youtube_id
    return songs


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
    else:
        songs = NovaScraper().scrap(ts_beg, ts_end)

    logger.info("Construit la playlist de " + str(options.titles) + " titres")
    songs = buildPlaylist(songs, options.titles, options.strategy)

    logger.info("Récupère les liens YouTube")
    songs = scrapYouTube(songs)

    logger.info("Clean les anciens et télécharge les nouveaux .mp3")
    songs = downloadMP3(options.youtube_dl_bin, working_directory, songs)

    logger.info("Construit le fichier de playlist")
    makePlaylistFile(songs, working_directory)

    if not options.no_upload:
        syncDropBox(songs, working_directory)

    logger.info("Update terminé !")
