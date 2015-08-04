# -*- coding: utf-8 -*-

import datetime
import logging
import requests
import time
from bs4 import BeautifulSoup

from Scraper import Scraper
from novaplaylist.core.Song import Song

logger = logging.getLogger('nova-playlist')


class FipScraper(Scraper):
    def parse(self, url):
        soup = BeautifulSoup(requests.get(url).json()[1]['data'])
        songs = []
        if not soup:
            return songs
        divs = soup.select("div.son")
        for div in divs:
            titles = div.select("p.titre_title")
            artists = div.select("p.titre_artiste")
            if titles and artists and titles[0].string != 'FIP ACTUALITE':
                songs.append(Song(
                    title=titles[0].string.title(),
                    artist=artists[0].string.title()
                ))
        return songs

    def scrap(self, ts_beg, ts_end):
        ts = ts_beg
        songs = []
        while ts < ts_end:
            url = 'http://www.fipradio.fr/fip_titres_diffuses/ajax/search/%s' % int(time.mktime(ts.timetuple()))
            songs.extend(self.parse(url))
            ts += datetime.timedelta(hours=1)
        return songs
