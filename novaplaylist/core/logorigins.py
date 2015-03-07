# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger("nova-playlist")
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger.setLevel(logging.DEBUG)
