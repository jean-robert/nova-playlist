# -*- coding: utf-8 -*-

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('nova-playlist')
logger.setLevel(logging.DEBUG)

import datetime
import eyed3
import os
import re
import requests
import requests_cache
import time
import urllib
from bs4 import BeautifulSoup

from optparse import OptionParser
from collections import Counter

logger.info("Update de nova-playlist")

parser = OptionParser()
parser.add_option("", "--log-level", dest="log_level", default="info", help="verbosity : debug, info, warning, error, critical")
parser.add_option("", "--log-filter", dest="log_filter", default="", help="")
parser.add_option("", "--lookback", dest="lookback", default=7 * 24 * 3600, type="int", help=u"Période en secondes")
parser.add_option("", "--titles", dest="titles", default=20, type="int", help=u"nombre de titres à sélectionner pour la playslist")
parser.add_option("", "--workspace", dest="workspace", default="")
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


class Song(object):
    def __init__(self, artist, title):
        self.artist = artist
        self.title = title

    def __repr__(self):
        return "%(artist)s - %(title)s" % self.__dict__

    def __eq__(self, other):
        return self.artist == other.artist and self.title == other.title

    def __hash__(self):
        return hash((self.artist, self.title))

    def tmp_filename(self, working_directory):
        return "%s/%s - %s.avi" % (working_directory, self.artist.replace("/", " "), self.title.replace("/", " "))

    def filename(self, working_directory):
        return "%s/%s - %s.mp3" % (working_directory, self.artist.replace("/", " "), self.title.replace("/", " "))

    def tag(self, working_directory, track_num):
        mp3 = eyed3.load(self.filename(working_directory))
        if mp3 is None:
            raise IOError("Cannot load id3 tags of %(self)s" % locals())
        mp3.initTag()
        mp3.tag.artist = self.artist
        mp3.tag.title = self.title
        mp3.tag.album = u"Nova Playlist %s" % datetime.date.today()
        mp3.tag.track_num = track_num
        mp3.tag.save()

    def download(self, youtube_dl_bin, working_directory):
        if not self.youtube_id:
            logger.warning("Song %(self)s has no youtube id" % locals())
        else:
            url = "https://www.youtube.com/watch?v=%s" % self.youtube_id
            tmp_fn = self.tmp_filename(working_directory)
            fn = self.filename(working_directory)
            if not os.path.exists(fn):
                os_query("""%(youtube_dl_bin)s --quiet --extract-audio --audio-format mp3 "%(url)s" -o "%(tmp_fn)s" """ % locals())
                logger.info("Downloaded %(self)s" % locals())
            else:
                logger.info("Skipped %(self)s, already downloaded" % locals())


def scrapNova(ts):
    mainUrl = "http://www.novaplanet.com/radionova/cetaitquoicetitre/"
    step = datetime.timedelta(seconds=3600)
    now = datetime.datetime.now()

    fullPlaylist = dict()
    while ts < now + step:
        url = mainUrl + str(int(time.mktime(ts.timetuple())))
        logger.info('Scrap actuellement @ %(ts)s, %(url)s' % locals())

        try:
            page = requests.get(url, timeout=15)
        except Exception as e:
            logger.error("Cannot get %(url)s, %(e)s" % locals())

        parsed_content = BeautifulSoup(page.content)
        for t in parsed_content.find_all('div', class_="resultat"):
            try:
                fullPlaylist[(t['class'][0]).split('_')[1]] = Song(artist=(t.h2.string if t.h2.string else t.h2.a.string).strip(),
                                                                   title=(t.h3.string if t.h3.string else t.h3.a.string).strip())
            except:
                logger.error("Cannot parse %(t)s, %(e)s" % locals())

        ts += step

    return fullPlaylist


def buildPlaylist(songs, title_nb):
    playlist = Counter(songs.values()).most_common(title_nb)
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
    for s, song in enumerate(songs):
        song.download(youtube_dl_bin, working_directory)
        song.tag(working_directory, s+1)


def makePlaylistFile(songs, working_directory):
    with open("%(working_directory)s/nova-playlist.m3u" % locals(), 'w+') as f:
        f.write("\n".join([song.filename(".") for song in songs]))


def syncDropBox(songs, working_directory):
    current_directory = os.path.dirname(os.path.abspath(__file__))
    os_query("%(current_directory)s/dropbox_uploader.sh delete music" % locals())
    os_query("%(current_directory)s/dropbox_uploader.sh mkdir music" % locals())
    os_query("%(current_directory)s/dropbox_uploader.sh upload %(working_directory)s/nova-playlist.m3u music" % locals())
    for song in songs:
        fn = song.filename(working_directory)
        if os.path.exists(fn):
            os_query("""%(current_directory)s/dropbox_uploader.sh upload "%(fn)s" music""" % locals())


def os_query(qry):
    start = time.time()
    retval = os.system(qry)
    duration = time.time() - start
    if retval:
        logger.error("[%(duration).2fs], retval=%(retval)s, %(qry)s" % locals())
        raise OSError("Cannot execute %(qry)s" % locals())
    else:
        logger.info("[%(duration).2fs], retval=%(retval)s, %(qry)s" % locals())


def remove_and_create_directory(directory):
    os_query("rm -rf %(directory)s" % locals())
    os_query("mkdir -p %(directory)s" % locals())


def create_directory(directory):
    os_query("mkdir -p %(directory)s" % locals())

if __name__ == "__main__":
    ts = datetime.datetime.now() - datetime.timedelta(seconds=options.lookback)
    ts = datetime.datetime(ts.year, ts.month, ts.day, ts.hour)

    working_directory = os.path.join(os.getcwd(), "music")
    if options.workspace:
        requests_cache.install_cache(options.workspace)

    logger.info("Scrap depuis %(ts)s" % locals())
    songs = scrapNova(ts)

    logger.info("Construit la playlist de " + str(options.titles) + " titres")
    songs = buildPlaylist(songs, options.titles)

    logger.info("Récupère les liens YouTube")
    songs = scrapYouTube(songs)

    logger.info("Clean les anciens et télécharge les nouveaux .mp3")
    downloadMP3(options.youtube_dl_bin, working_directory, songs)

    logger.info("Construit le fichier de playlist")
    makePlaylistFile(songs, working_directory)

    if not options.no_upload:
        syncDropBox(songs, working_directory)

    logger.info("Update terminé !")
