# -*- coding: utf-8 -*-

import datetime

from Scraper import Scraper
from novaplaylist.core.Song import Song


class FipScraper(Scraper):
    def parse(self, url):
        soup = self.get(url)
        songs = []
        if not soup:
            return songs
        divs = soup.select("div.son")
        for div in divs:
            if len(div.select("p.titre_title")) * len(div.select("p.titre_artiste")) > 0:
                songs.append(Song(
                    title=div.select("p.titre_title")[0].string.title(),
                    artist=div.select("p.titre_artiste")[0].string.title()
                ))
        return songs

    def scrap(self, ts_beg, ts_end):
        ts = ts_beg
        songs = []
        while ts < ts_end:
            url = "http://www.fipradio.fr/archives-antenne?start_date=%s&start_hour=%s" % (ts.strftime("%Y-%m-%d"), ts.hour)
            songs.extend(self.parse(url))
            ts += datetime.timedelta(hours=1)
        return songs
