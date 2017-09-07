import ripe.atlas.cousteau.exceptions as racEx
from ripe.atlas.cousteau import AtlasStream
from warriorpy.shorthand import diriofile as df
from collections import defaultdict
from functools import wraps
import time
import ripe_api as ra
import threading
from warriorpy.shorthand import looplist

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
    def __init__(self, probe_list, meas_seq, reps, max_threads=1,
            init_kwargs=[None]):
        '''
        :param probe_list: list of probe IDs (int) for experiment
        :param meas_seq: (ordered) list of functions to perform on each probe.
        The kwargs input of each successive function should be the output of its
        predecessor.
        :param reps: the number of experiments to run on each probe
        :max threads: the number of experiments to run in parallel
        :init_kwargs: a list of kwargs (dicts) for the first function in
        meas_seq, such that the nth rep gets the nth kwargs from init_kwargs
        as input for its 0th function. If len(init_kwargs) < reps, the
        init_kwargs will modular repeat

        data from the experiment is stored in self.meas_data in the following
        format: {meas_seq step: {probe id: [0th rep, 1st rep, ..., nth rep]}}
        '''
        self.probe_list = probe_list
        self.meas_seq = meas_seq
        self.meas_state = list()
        self.meas_data = dict()
        self.max_reps = reps
        self.meas_state[0] = set(probe_list)
        self.sem = threading.Semaphore(max_threads)
        self.lv = threading.Lock()
        self.init_kwargs = looplist.looplist(init_kwargs)
        if len(self.init_kwargs) == 0:
            self.init_kwargs.append(None)


    def run(self):
        reps = 0
        steps = len(self.meas_state)
        while reps < self.max_reps:
            for probe in self.probe_list:
                self.sem.acquire()
                threading.Thread(target=self.run_meas_seq, args=(self),
                        kwargs={'probe':probe, 'kwargs':init_kwargs[reps]})


    def run_sets(self):
        reps = 0
        steps = len(self.meas_state)
        for probe in self.probe_list:
            while reps < self.max_reps:
                self.sem.acquire()
                threading.Thread(target=self.run_meas_seq, args=(self),
                        kwargs={'probe':probe, 'kwargs':init_kwargs[reps]})


    def run_meas_seq(self, probe, kwargs):
        for i, meas_func in enumerate(self.meas_seq):
            step = 'step_'+str(i)
            if i == 0:
                data = meas_func(probe)
            else:
                kwargs = self.meas_data[step][probe][-1]
                data = meas_func(probe, kwargs**)
            self.lv.acquire()
            # dump data to self.meas_data
            if step not in self.meas_data:
                self.meas_data[step] = dict()
            if probe not in self.meas_data[step]:
                self.meas_data[step][probe] = list()
            self.meas_data[step][probe].append(data)
            self.lv.release()
            if data is None:
                break
        self.sem.release()
