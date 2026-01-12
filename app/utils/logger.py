# app/utils/logger.py
# Simple structured logger using stdlib logging

import logging
import sys

logger = logging.getLogger("nano_convert_backend")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# expose convenience functions
def debug(msg: str):
    logger.debug(msg)

def info(msg: str):
    logger.info(msg)

def warn(msg: str):
    logger.warning(msg)

def error(msg: str):
    logger.error(msg)
