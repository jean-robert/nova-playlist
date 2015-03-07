# -*- coding: utf-8 -*-

from mutagen.id3 import ID3, TIT2, TPE1, TALB
import os

from logorigins import logger
from tools import os_query


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
        ret = u"%s - %s.avi" % (self.artist.replace("/", " "), self.title.replace("/", " "))
        return os.path.join(working_directory, ret)

    def filename(self, working_directory):
        ret = u"%s - %s.mp3" % (self.artist.replace("/", " "), self.title.replace("/", " "))
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
