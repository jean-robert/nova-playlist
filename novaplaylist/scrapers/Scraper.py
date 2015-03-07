# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup

from novaplaylist.core.logorigins import logger


class Scraper(object):
    def get(self, url):
        try:
            logger.info("Scraping %(url)s" % locals())
            ret = requests.get(url)
            soup = BeautifulSoup(ret.content)
            return soup
        except Exception as e:
            logger.error("Cannot scrap %(url)s, %(e)s" % locals())

    def post(self, url, data):
        try:
            logger.info("Scraping %(url)s" % locals())
            ret = requests.post(url, data)
            soup = BeautifulSoup(ret.content)
            return soup
        except Exception as e:
            logger.error("Cannot scrap %(url)s, %(e)s" % locals())
