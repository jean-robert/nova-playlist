# -*- coding: utf-8 -*-

import logging
import sys
from colorlog import ColoredFormatter

loggers = ('nova-playlist',)
formatter = ColoredFormatter(
    '%(log_color)s%(asctime)s.%(msecs)03d, %(name)s, %(levelname)s, %(message)s',
    log_colors={
        'DEBUG': 'green',
        'INFO': 'blue',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_purple',
    },
    datefmt='%Y-%m-%d %H:%M:%S'
)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
for logger in map(logging.getLogger, loggers):
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
