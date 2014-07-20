from . import core
from . import utils


# Absolute path to gridbots top level directory
import os
path = os.path.dirname(os.path.realpath(__file__))


# Set up logging
import logging
logging.basicConfig(format='%(message)s', level=logging.DEBUG)
