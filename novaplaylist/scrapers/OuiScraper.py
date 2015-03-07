# -*- coding: utf-8 -*-

import time
import datetime

from Scraper import Scraper
from novaplaylist.core.Song import Song
from novaplaylist.core.logorigins import logger


class OuiScraper(Scraper):
    def parse(self, url, songs):
        soup = self.get(url)
        for t in soup.select('div#cest-quoi-ce-titre-results li'):
            try:
                key = t.select(".date")[0].string
                songs[key] = Song(
                    artist=t.select(".artist")[0].string.title(),
                    title=t.select(".title")[0].string.title()
                )
            except Exception as e:
                logger.error("Cannot parse %(t)s, %(e)s" % locals())

    def scrap(self, ts_beg, ts_end):
        url = "https://www.ouifm.fr/cest-quoi-ce-titre/?flux=rock&date=%Y%m%d&time=%H%M"
        ts = ts_beg

        songs = dict()
        while ts < ts_end:
            self.parse(ts.strftime(url), songs)
            ts += datetime.timedelta(minutes=30)
        return songs.values()
