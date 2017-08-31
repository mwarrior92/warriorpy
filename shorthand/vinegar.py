try:
    import cPickle as pickle
except:
    import pickle
from functools import wraps
import os
from warriorpy.shorthand import diriofile as df
import time

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
#                       GLOBAL AND SETUP
##################################################################

basedir = df.rightdir(os.getcwd())
cachedir = basedir # manually change this in the file that is using vinegar
datadir = df.rightdir(cachedir+"cache/")

##################################################################
#                           CODE
##################################################################

def set_cache_dir(f):
    global cachedir
    cachedir = f
    global datadir
    datadir = df.rightdir(cachedir+"cache/")


def cache_me_outside(func):
    @wraps(func)
    def but_im_not_a_rapper(*args, **kwargs):
        pf = cachedir+func.__name__+".pickle"
        try:
            cache = df.picklein(pf)
            if cache is None:
                cache = dict()
        except Exception as e:
            logger.error("exception:"+str(e))
            cache = dict()

        invals = df.make_hashable(list(args) + zip(kwargs.keys(), kwargs.values()))
        dcache = None
        if invals in cache:
            # use indirection so that the main cache file doesn't get enormous
            dataf = cache[invals]
            try:
                dcache = df.picklein(dataf)
                logger.warning("used cached return value for "+func.__name__)
            except Exception as e:
                logger.error("exception:"+str(e))

        if dcache is not None:
            return dcache

        logger.debug("cache miss")
        dcache = func(*args, **kwargs)
        # reload outer cache file just in case it was modified in executing func
        # (for recursive functions)
        try:
            cache = df.picklein(pf)
            if cache is None:
                cache = dict()
        except Exception as e:
            logger.error("exception:"+str(e))
            cache = dict()
        dataf = datadir+func.__name__+"_"+str(time.time())+".pickle"
        cache[invals] = dataf
        df.pickleout(pf, cache)
        df.pickleout(dataf, dcache)
        return dcache
    return but_im_not_a_rapper
