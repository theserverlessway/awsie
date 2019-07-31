import logging
import sys

__version__ = '0.4.0'

logger = logging.getLogger('awsie')
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
