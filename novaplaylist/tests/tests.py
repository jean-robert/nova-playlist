# -*- coding: utf-8 -*-

import os
import datetime
import requests_cache
import unittest
from novaplaylist.core.tools import parse_duration, os_query, remove_and_create_directory, create_directory, clean_filename
from novaplaylist.core.Song import Song
from novaplaylist.scrapers import Scraper, FipScraper, NovaScraper, OuiScraper, NostalgieScraper


class ToolsTest(unittest.TestCase):
    def test_all(self):
        self.assertEqual(clean_filename("ta"), "ta")
        self.assertEqual(clean_filename("t/a"), "t a")
        self.assertEqual(clean_filename("t$a"), "t a")
        self.assertEqual(parse_duration("1d"), 86400)
        self.assertEqual(parse_duration("100"), 100)
        self.assertRaises(TypeError, parse_duration, 1)
        self.assertRaises(OSError, os_query, "exit 1")
        self.assertEqual(os_query("exit 0"), None)


class SongTest(unittest.TestCase):
    def test_all(self):
        song = Song("Artist", "Title")
        self.assertEqual(song, Song("Artist", "Title"))
        self.assertEqual(hash(song), -7098157806416884659)
        self.assertNotEqual(song, Song("Artist", ""))
        self.assertNotEqual(song, 1)
        self.assertEqual(song.tmp_filename(""), "Artist - Title.avi")
        self.assertEqual(song.tmp_filename("/tmp"), "/tmp/Artist - Title.avi")
        self.assertEqual(song.tmp_filename("/tmp/"), "/tmp/Artist - Title.avi")
        self.assertEqual(song.filename(""), "Artist - Title.mp3")
        self.assertEqual(song.filename("/tmp"), "/tmp/Artist - Title.mp3")
        self.assertEqual(song.filename("/tmp/"), "/tmp/Artist - Title.mp3")
        directory = os.path.join(os.path.dirname(__file__), "tmp")
        self.assertEqual(create_directory(directory), None)
        self.assertEqual(remove_and_create_directory(directory), None)
        os_query("rm -rf %(directory)s" % locals())


class ScraperTest(unittest.TestCase):
    def setUp(self):
        requests_cache.install_cache(
            cache_name=os.path.join(os.path.dirname(__file__), "test"),
            allowable_methods=('GET', 'POST')
        )
        self.ts_beg = datetime.datetime(2015, 3, 5, 0)
        self.ts_end = datetime.datetime(2015, 3, 5, 3)

    def test_base(self):
        scraper = Scraper()
        self.assertEqual(scraper.get(""), None)
        self.assertEqual(scraper.post("", {}), None)

    def test_fip(self):
        scraper = FipScraper()
        songs = scraper.parse("http://www.fipradio.fr/archives-antenne?start_date=2015-03-05&start_hour=1")
        self.assertEqual(len(songs), 14)
        self.assertEqual(songs[5], Song("Brigitte", "Embrassez Vous"))
        songs = scraper.scrap(self.ts_beg, self.ts_end)
        self.assertEqual(len(songs), 41)

    def test_nova(self):
        scraper = NovaScraper()
        songs = scraper.scrap(self.ts_beg, self.ts_end)
        self.assertEqual(len(songs), 45)
        self.assertEqual(songs[0], Song("Sporto Kantes", "Holiday"))

    def test_oui(self):
        scraper = OuiScraper()
        songs = scraper.scrap(self.ts_beg, self.ts_end)
        self.assertEqual(len(songs), 32)
        self.assertEqual(songs[0], Song("Every Time I Die", "The New Black"))

    def test_nostalgie(self):
        scraper = NostalgieScraper()
        songs = scraper.scrap(self.ts_beg, self.ts_end)
        self.assertEqual(len(songs), 47)
        self.assertEqual(songs[0], Song("Roger Glover", "Love Is All"))
