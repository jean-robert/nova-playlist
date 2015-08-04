# -*- coding: utf-8 -*-

import datetime
import math

from Scraper import Scraper
from novaplaylist.core.Song import Song
from novaplaylist.core.logorigins import logger


class RadioparadiseScraper(Scraper):
    def parse(self, url, songs):
        soup = self.get(url)
        if not soup:
            return
        for t in soup.find(id="content").select("a"):
            song = Song(
               artist=t.text.split(' - ')[1],
               title=t.text.split(' - ')[0]
            )

    def scrap(self, ts_beg, ts_end):
        songs = dict()
        offset = int((math.ceil((datetime.datetime.now() - ts_beg).total_seconds() / 3600 / 6) - 1) * 6)
        ts = datetime.datetime.now() - datetime.timedelta(hours=offset+6)

        while ts < ts_end:
            url = "http://www.radioparadise.com/rp2-content.php?name=Playlist&offset=%s" % str(offset)
            self.parse(url, songs)
            offset -= 6
            ts = datetime.datetime.now() - datetime.timedelta(hours=offset+6)

        return songs.values()
