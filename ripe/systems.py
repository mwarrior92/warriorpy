import ripe.atlas.cousteau.exceptions as racEx
from ripe.atlas.cousteau import AtlasStream
from warriorpy.shorthand import diriofile as df
from collections import defaultdict
from functools import wraps
import time
import ripe_api as ra
import threading

##################################################################
#                           DESCRIPTION
##################################################################
'''
a system for performing sequential, interdependent measurements over RIPE Atlas.
For example, if a ping query requires the results of a DNS result, you could
feed a measurement_droid a list of functions [do_dns, do_ping] where the
parameter of do_ping() is the result from do_dns.

NOTE: you must write the functions; this is only a wrapper to easily allow them
to happen in an event driven sequence, such that function i+1 is essentially a
callback for function i

NOTE: the input to function i+1 will always be the list of results from function
i

NOTE: the first function in the sequence has no parameters

NOTE: you can feed up to
'''


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
#                        GLOBAL AND SETUP
##################################################################

# paths
basedir = df.getdir(__file__)+'../'
statedir = df.rightdir(basedir+'state/')
rawdirlist = df.getlines(basedir+'state/datapaths.list')
datafiles = df.listfiles(basedir+rawdirlist[0], fullpath=True)
plotsdir = df.rightdir(basedir+"plots/")

##################################################################
#                           CODE
##################################################################

# wrapper to deploy an individual measurement

# wrapper to manage sequence of measurements for an individual probe

# wrapper to manage experiment (high level)

class ripe_experiment:
    def __init__(self, probe_list, meas_seq, reps, max_threads=1):
        self.probe_list = probe_list
        self.meas_seq = meas_seq
        self.meas_state = list()
        self.meas_data = dict()
        self.max_reps = reps
        self.meas_state[0] = set(probe_list)
        self.sem = threading.Semaphore(max_threads)
        self.lv = threading.Lock()

    def run(self):
        reps = 0
        steps = len(self.meas_state)
        while reps < self.max_reps:
            for probe in self.probe_list:
                self.sem.acquire()
                threading.Thread(target=self.run_meas_seq, args=(self),
                        kwargs={'probe':probe})


    def run_meas_seq(self, probe):
        for i, meas_func in enumerate(self.meas_seq):
            step = 'step_'+str(i)
            if i == 0:
                data = meas_func(probe)
            else:
                kwargs = self.meas_data[step][probe][-1]
                data = meas_func(probe, kwargs**)
            self.lv.acquire()
            # dump data to self.meas_data
            if probe not in self.meas_data:
                pass
            self.lv.release()
            if data is None:
                break
        self.sem.release()
