'''
    Marc Warrior put this code together, with some help from various entities
    on the internet (stack exchange). See README for overview; descriptions are
    also in comments of the code. Contact Marc at warrior@u.northwestern.edu
'''
import os
import shutil
import tarfile
import cPickle as pickle
from collections import defaultdict as ddict
from bs4 import BeautifulSoup
import json
import time
import math

##################################################################
#                           LOGGING
##################################################################
import logging
import logging.config

logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

# create logger
logger = logging.getLogger(__name__)
logger.debug(__name__+"logger loaded")

##################################################################
#          FILE & DIR MANAGEMENT & NAVIGATION
##################################################################

# https://stackoverflow.com/questions/365826/calculate-distance-between-2-gps-coordinates
def latlong_distance_km(c1, c2, radius=6371):
    lat1, long1 = c1
    lat2, long2 = c2
    dlat = math.radians(lat2-lat1)
    dlong = math.radians(long2-long1)
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    a = (math.sin(dlat/2)**2)+(math.sin(dlong/2)**2)*(math.cos(lat1)*math.cos(lat2))
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return radius*c


