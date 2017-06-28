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


# class to make reading a file line by line look cleaner in code
class linereader:
    def __init__(self, filename):
        self.filename = filename
        self.gotmore = True
        self.current_txt = ""
        try:
            self.f = open(filename, 'r')
            logger.debug("opened "+self.filename)
            self.next_txt = self.f.readline()
        except IOError:
            logger.error('IOError reading '+filename)

    def getnext(self):
        if self.gotmore:
            self.current_txt = self.next_txt
            try:
                self.next_txt = self.f.readline()
            except IOError:
                logger.error('IOError reading '+filename)
            if self.next_txt == "":
                self.gotmore = False
        else:
            self.current_txt = ""
        return self.current_txt

    def __del__(self):
        self.f.close()
        logger.debug("closed "+self.filename)
