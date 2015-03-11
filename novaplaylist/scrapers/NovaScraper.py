# -*- coding: utf-8 -*-

import time
import datetime

from Scraper import Scraper
from novaplaylist.core.Song import Song
from novaplaylist.core.logorigins import logger


class NovaScraper(Scraper):
    def parse(self, url, songs):
        soup = self.get(url)
        if not soup:
            return
        for t in soup.select('div.resultat'):
            try:
                songs[(t['class'][0]).split('_')[1]] = Song(
                    artist=(t.h2.string if t.h2.string else t.h2.a.string).strip(),
                    title=(t.h3.string if t.h3.string else t.h3.a.string).strip()
                )
            except Exception as e:
                logger.error("Cannot parse %(t)s, %(e)s" % locals())

    def scrap(self, ts_beg, ts_end):
        url = "http://www.novaplanet.com/radionova/cetaitquoicetitre/%i"
        ts = ts_beg

        songs = dict()
        while ts < ts_end:
            timestamp = (ts - datetime.datetime(1970, 1, 1)).total_seconds() - 3600
            self.parse(url % timestamp, songs)
            ts += datetime.timedelta(hours=1)
        return songs.values()
