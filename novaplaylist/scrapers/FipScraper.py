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
    def parse(self, url, data):
        soup = BeautifulSoup(requests.post(url, data).json()[1]['data'])
        songs = []
        if not soup:
            return songs
        divs = soup.select("div.son")
        for div in divs:
            subdiv = div.select("div.list-song-right")[0].select("div.texte")[0]
            titles = subdiv.select("p.titre_title")
            artists = subdiv.select("p.titre_artiste")
            if titles and artists and titles[0].string != 'FIP ACTUALITE':
                songs.append(Song(
                    title=titles[0].string.title().strip(),
                    artist=artists[0].get_text()[5:].strip()
                ))
        return songs

    def scrap(self, ts_beg, ts_end):
        ts = ts_beg
        songs = []
        while ts < ts_end:
            url = 'http://www.fipradio.fr/system/ajax/'
            data = {'display_search': 1,
                    'select_radio': 7,
                    'select_jour': int(time.mktime(datetime.datetime(ts.year, ts.month, ts.day).timetuple()) - \
                                       time.mktime(datetime.datetime(1970, 1, 1).timetuple()) - \
                                       3600),
                    'select_heure': ts.hour,
                    'select_minute': ts.minute,
                    'form_build_id': 'form-md8wUEVgOEDkqf-6e7IqXdpoYrgaS2bYPCFTtbIQ22k',
                    'form_id': 'fip_titres_diffuses_cruiser_form_search_date'}
            songs.extend(self.parse(url, data))
            ts += datetime.timedelta(hours=1)
        return songs
