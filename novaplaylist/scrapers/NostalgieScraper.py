# -*- coding: utf-8 -*-

import time
import datetime

from Scraper import Scraper
from novaplaylist.core.Song import Song
from novaplaylist.core.logorigins import logger


class NostalgieScraper(Scraper):
    def parse(self, url, data, songs):
        soup = self.post(url, data)
        for t in soup.select('div.item')[1:]:
            hour = t.select(".hour")
            if not hour:
                continue
            song = Song(
                artist=t.select(".artist")[0].get_text().strip(),
                title=t.select(".track")[0].get_text().strip().title()
            )
            if song.artist != "Nostalgie":
                songs[hour[0].string] = song

    def scrap(self, ts_beg, ts_end):
        url = "http://www.nostalgie.fr/radio-421/titres-diffuses-431/titresdiffuses/rechercherdate/"
        ts = ts_beg

        songs = dict()
        while ts < ts_end:
            data = {
                "annee": ts.year,
                "mois": ts.month,
                "jour": ts.day,
                "heure": ts.hour,
                "minute": ts.minute
            }
            self.parse(url, data, songs)
            ts += datetime.timedelta(minutes=20)
        return songs.values()
