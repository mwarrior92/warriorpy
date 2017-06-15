'''
    Marc Warrior put this code together, with some help from various entities
    on the internet (stack exchange).
'''
import logging
import logging.config

##################################################################
#                           LOGGING
##################################################################

logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

# create logger
logger = logging.getLogger(__name__)
logger.debug(__name__+"logger loaded")


# use a file like a python list (array)
class linefile:
    def __init__(self, filename):
        self.filename = filename
        self.nextline = 0
        self.filesize = 0
        self.current_txt = ''
        self.currentline = -1
        try:
            f = open(filename, 'r')
            logger.debug("opened "+self.filename)
            try:
                for line in f:
                    self.filesize += 1
            finally:
                f.close()
                logger.debug("closed "+self.filename)
        except IOError:
            logger.error('IOError reading '+filename)

    def __getitem__(self, item):
        try:
            f = open(self.filename, 'r')
            logger.debug("opened "+self.filename)
            try:
                if item < self.filesize:
                    for ind, line in enumerate(f):
                        if ind == item:
                            res = line
                            break;
            finally:
                f.close()
                logger.debug("closed "+self.filename)
        except IOError:
            res = None
            logger.error('IOError reading '+self.filename)
        logger.debug("read from "+self.filename)
        return res

    def getnext(self):
        self.current_txt = self[self.nextline]
        if self.current_txt is not None:
            self.nextline += 1
            self.currentline += 1
        return self.current_txt
