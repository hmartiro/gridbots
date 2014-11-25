"""

"""

__title__ = 'gridbots'
__version__ = '0.1.0'
__author__ = 'Hayk Martirosyan'
__license__ = 'Apache2'
__copyright__ = '2014 Hayk Martirosyan'


from . import core
from . import utils


# Absolute path to gridbots top level directory
import os
path = os.path.dirname(os.path.realpath(__file__))


# Set up logging
import logging
logging.basicConfig(format='%(message)s', level=logging.DEBUG)
