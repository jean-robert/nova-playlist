# -*- coding: utf-8 -*-

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('nova-playlist')
logger.setLevel(logging.DEBUG)

import datetime
import json
from mutagen.id3 import ID3, TIT2, TPE1, TALB
from mutagenerate.core import AmazonSource
import os
import random
import re
import requests
import requests_cache
import time
import urllib
from bs4 import BeautifulSoup

from optparse import OptionParser
from collections import Counter

import youtubeCredentials

logger.info("Update de nova-playlist")

parser = OptionParser()
parser.add_option("", "--log-level", dest="log_level", default="info", help="verbosity : debug, info, warning, error, critical")
parser.add_option("", "--log-filter", dest="log_filter", default="", help="")
parser.add_option("", "--lookback", dest="lookback", default="7d", help=u"Période en secondes")
parser.add_option("", "--strategy", dest="strategy", default="mostcommon", help=u"Stratégie parmi (mostcommon, random)")
parser.add_option("", "--titles", dest="titles", default=20, type="int", help=u"Nombre de titres à sélectionner pour la playslist")
parser.add_option("", "--output", dest="output", default="mp3", help=u"Type d'output (mp3, channel)")
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


source = AmazonSource()


class Song(object):
    def __init__(self, artist, title):
        self.artist = artist
        self.title = title

    def __unicode__(self):
        return u"%(artist)s - %(title)s" % self.__dict__

    def __repr__(self):
        return self.__unicode__().encode("utf8")

    def __eq__(self, other):
        return self.artist == other.artist and self.title == other.title

    def __hash__(self):
        return hash((self.artist, self.title))

    def tmp_filename(self, working_directory):
        return u"%s/%s - %s.avi" % (working_directory, self.artist.replace("/", " "), self.title.replace("/", " "))

    def filename(self, working_directory):
        return u"%s/%s - %s.mp3" % (working_directory, self.artist.replace("/", " "), self.title.replace("/", " "))

    def tag(self, working_directory, track_num):
        mp3 = ID3(self.filename(working_directory))
        if mp3 is None:
            raise IOError("Cannot load id3 tags of %(self)s" % locals())
        mp3.add(TIT2(encoding=3, text=self.title))
        mp3.add(TPE1(encoding=3, text=self.artist))
        mp3.add(TALB(encoding=3, text=u"Nova Playlist"))
        mp3.save()
        source.generate_and_save(mp3, update=False, yes=True)

    def download(self, youtube_dl_bin, working_directory):
        if not self.youtube_id:
            logger.warning("Song %(self)s has no youtube id" % locals())
        else:
            url = "https://www.youtube.com/watch?v=%s" % self.youtube_id
            tmp_fn = self.tmp_filename(working_directory).encode("utf8")
            fn = self.filename(working_directory).encode("utf8")
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
        for t in parsed_content.select('div.resultat'):
            try:
                fullPlaylist[(t['class'][0]).split('_')[1]] = Song(artist=(t.h2.string if t.h2.string else t.h2.a.string).strip(),
                                                                   title=(t.h3.string if t.h3.string else t.h3.a.string).strip())
            except:
                logger.error("Cannot parse %(t)s, %(e)s" % locals())

        ts += step
    return fullPlaylist.values()


def buildPlaylist(songs, title_nb, strategy):
    playlist = Counter(songs).most_common()
    if strategy == "random":
        random.shuffle(playlist)
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
    for s, song in enumerate(songs):
        song.download(youtube_dl_bin, working_directory)
        song.tag(working_directory, s + 1)


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


def getAccessToken():
    payload = {'client_id': youtubeCredentials.clientID,
               'client_secret': youtubeCredentials.clientSecret,
               'refresh_token': youtubeCredentials.refreshToken,
               'grant_type': 'refresh_token'}
    r = requests.post('https://accounts.google.com/o/oauth2/token', data=payload)
    return r.json()['access_token']


def cleanChannelPlaylist(token):
    headers = {'Authorization':  'Bearer ' + token}
    url = 'https://www.googleapis.com/youtube/v3/playlistItems'
    r = requests.get(url, params={'part': 'snippet',
                                  'playlistId': youtubeCredentials.playlistId,
                                  'maxResults': 50}, headers=headers)
    for video in r.json()['items']:
        vd = requests.delete(url, params={'id': video['id']}, headers=headers)
        if vd.status_code != 204:
            logger.error("Error removing song from playlist %s" % (vd.text))


def buildChannelPlaylist(token, songs):
    url = 'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet'
    headers = {'Authorization':  'Bearer ' + token,
               'Content-Type': 'application/json'}
    songPosition = -1
    for song in songs:
        if song.youtube_id:
            songPosition += 1
            payload = json.dumps({'snippet':
                                  {
                                      'playlistId': youtubeCredentials.playlistId,
                                      'resourceId': {
                                          'kind': 'youtube#video',
                                          'videoId': song.youtube_id
                                      },
                                      'position': songPosition
                                  }
                              })
            logger.debug('Sending payload %s' % (payload))
            r = requests.post(url, data=payload, headers=headers)
            if r.status_code != 200:
                logger.error("Error publishing %s : %s" % (song.artist + ' / ' + song.title, r.text))


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


duration_suffixes = dict((("s", 1), ("m", 60), ("h", 60 * 60), ("d", 24 * 60 * 60),
                         ("w", 7 * 24 * 60 * 60), ("y", 365 * 7 * 24 * 60 * 60)))


def parse_duration(duration):
    """
        Parse human duration into duration in seconds
    """
    if not isinstance(duration, str) and not isinstance(duration, unicode):
        raise TypeError("Cannot parse duration. Must be string or unicode")
    if duration.isdigit():
        return int(duration)
    suffix = duration[-1]
    prefix = duration[:-1]
    return int(prefix) * duration_suffixes[suffix]

if __name__ == "__main__":
    lookback = parse_duration(options.lookback)
    ts = datetime.datetime.now() - datetime.timedelta(seconds=lookback)
    ts = datetime.datetime(ts.year, ts.month, ts.day, ts.hour)

    working_directory = os.path.join(os.getcwd(), "music")
    if options.workspace:
        requests_cache.install_cache(options.workspace)

    logger.info("Scrap depuis %(ts)s" % locals())
    songs = scrapNova(ts)

    logger.info("Construit la playlist de " + str(options.titles) + " titres")
    songs = buildPlaylist(songs, options.titles, options.strategy)

    logger.info("Récupère les liens YouTube")
    songs = scrapYouTube(songs)

    if options.output == 'mp3':
        logger.info("Clean les anciens et télécharge les nouveaux .mp3")
        downloadMP3(options.youtube_dl_bin, working_directory, songs)

        logger.info("Construit le fichier de playlist")
        makePlaylistFile(songs, working_directory)

        if not options.no_upload:
            syncDropBox(songs, working_directory)

    if options.output == 'channel':
        logger.info("Authentification sur YouTube")
        accessToken = getAccessToken()

        logger.info("Clean la playlist actuelle")
        cleanChannelPlaylist(accessToken)

        logger.info("Construit la nouvelle playlist sur le channel")
        buildChannelPlaylist(accessToken, songs)

    logger.info("Update terminé !")
