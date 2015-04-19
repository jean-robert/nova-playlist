# -*- coding: utf-8 -*-

from mutagen.id3 import ID3, TIT2, TPE1, TALB
import os

from logorigins import logger
from tools import os_query, clean_filename
from youtubeapi import ytapi

class Song(object):
    def __init__(self, artist, title):
        self.artist = artist
        self.title = title

    def __unicode__(self):
        return u"%(artist)s - %(title)s" % self.__dict__

    def __repr__(self):
        return self.__unicode__().encode("utf8")

    def __eq__(self, other):
        return isinstance(other, Song) and self.artist == other.artist and self.title == other.title

    def __hash__(self):
        return hash((self.artist, self.title))

    def tmp_filename(self, working_directory):
        ret = u"%s - %s.avi" % (clean_filename(self.artist), clean_filename(self.title))
        return os.path.join(working_directory, ret)

    def filename(self, working_directory):
        ret = u"%s - %s.mp3" % (clean_filename(self.artist), clean_filename(self.title))
        return os.path.join(working_directory, ret)

    def tag(self, working_directory, track_num, source):
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

    def searchYouTubeId(self):
        try:
            yta = ytapi()
            youtube_id = yta.searchVideoId(str(self))
            if youtube_id:
                logger.info("Found %(youtube_id)s for song %(song)s" % locals())
            else:
                logger.warning("No youtube id found for song %(song)s" % locals())
            self.youtube_id = youtube_id

        except:
            logger.warning('YouTube API search error, fallback on scraper')
            self.scrapYouTubeId()

    def scrapYouTubeId(self):
        url = "http://www.youtube.com/results?search_query=%s" % urllib.quote_plus(str(self))
        page = requests.get(url, timeout=15)

        if 'Aucune vid' in page.content:
            logger.warning("No video found for %(song)s" % locals())
            self.youtube_id = None
        else:
            youtube_id = re.findall('href="\/watch\?v=(.*?)[&;"]', page.content)[0]
            logger.info("Found %(youtube_id)s for song %(song)s" % locals())
            self.youtube_id = youtube_id
