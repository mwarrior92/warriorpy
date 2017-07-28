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


def deploy_measurement(mdroid):
    request = mdroid.get_request()
    th = mdroid.get_thread_handler()
    is_success, measids = ra.send_request(request)
    if is_success:
        mdroid.success_handler(measids)
        for m in measids:
            th.push_listen(mdroid)
    else:
        mdroid.fail_handler()


class measurement_droid:
    def __init__(self, mseq, tman):
        self.mseq = mseq # message_sequence
        self.tman = tman # thread_manager
        self.result_sets = list()

        func = self.mseq.get_next_step()
        request = func()
        self.push_request(request)


    def get_thread_handler(self):
        return self.tman


    def success_handler(self, measids):
        self.mseq.started(measids)


    def fail_handler(self, req):
        pass


    def response_handler(self, resp):
        measid = resp['measid']
        done, results = self.mseq.finished(measid, resp)
        if done:
            self.result_lists.append(results)
        func = self.mseq.get_next_step()
        request = func(results)
        self.current_request = request
        if request is not None:
            self.tman.push_request(self)


def do_nothing(arg):
    return None


class measurement_sequence:
    def __init__(self, seq):
        self.seq = seq # function list; should end with do_nothing
        self.step = 0
        self.doing = set()
        self.results = defaultdict(list)
        self.lock = threading.Lock()
        self.cond = threading.Condition(self.lock)


    def started(self, measids):
        self.doing = set(measids)


    def finished(self, measid, result):
        self.cond.acquire()
        self.results[self.step].append(result)
        results = self.results[self.step]
        if measid in self.doing:
            self.doing.remove(measid)
        if len(self.doing) == 0:
            done = True
        else:
            done = False
        self.cond.release()
        return done, results


    def get_next_step(self):
        self.cond.acquire()
        func = self.seq[self.step]
        self.step += 1
        self.cond.release()
        return func


def worker(pool):
    d = None
    pool.lock()
    d = pool.pop()
    pool.unlock()
    if d is not None:
        deploy_measurement(d['request'], d['mdroid'])
    d['mdroid'].tman.stir_pools()


class workpool:
    def __init__(self):
        self.items = list()
        self.my_lock = threading.Lock()
        self.cond = threading.Condition(self.lock)


    def lock(self):
        self.cond.acquire()


    def unlock(self):
        self.cond.release()


    def wait(self, timeout=None):
        self.cond.wait(timeout)


    def notify(self, n=1):
        if self.lock.locked():
            self.cond.notify(n)
        else:
            logger.error("bad code: tried to notify without locking")


    def notify_all(self):
        if self.lock.locked():
            self.cond.notify_all()
        else:
            logger.error("bad code: tried to notify all without locking")


    def push(self, item):
        if self.lock.locked():
            self.items.append(item)
        else:
            logger.error("bad code: tried to push to pool without locking")


    def pop(self):
        if self.lock.locked():
            if len(self.items) > 0:
                item = self.items.pop(0)
                return item
            else:
                return None
        else:
            logger.error("bad code: tried to pop from pool without locking")


    def get_len(self):
        if self.lock.locked():
            length = len(self.items)
        else:
            logger.error("bad code: tried to get pool length without locking")


    def __len__(self):
        return self.get_len()


class thread_manager:
    def __init__(self, max_threads, request_pool):
        self.max_threads = max_threads
        self.request_list = list()
        self.listener_list = list()
        self.request_lock = list()
        self.listen_lock = list()
        self.request_cond = threading.Condition(self.request_lock)
        self.listen_cond = threading.Condition(self.listen_lock)
        self.threads = list()
        self.keep_going = True
        self.busy_threads = 0

        self.start_threads()


    def busy_wait(self):
        while self.busy_threads > self.max_threads - 1:
            time.sleep(10*(1+self.busy_threads))


    def start_threads(self):
        while threading.active_count() < self.max_threads / 2:
            self.threads.append(threading.Thread(target=self.worker))
            self.threads[-1].daemon = True
            self.threads[-1].start()

        while threading.active_count() < self.max_threads / 2:
            self.threads.append(threading.Thread(target=self.listener))
            self.threads[-1].daemon = True
            self.threads[-1].start()


    def push_request(self, mdroid):
        if self.request_lock.locked():
            self.request_list.append(mdroid)
            self.request_cond.notify()
        else:
            logger.error("bad code: tried to push to request list without\
                    locking")


    def push_listen(self, mdroid):
        if self.listen_lock.locked():
            self.listen_list.append(mdroid)
        else:
            logger.error("bad code: tried to push to request list without\
                    locking")


    def worker(self):
        on = False
        while self.keep_going:
            self.request_cond.acquire() #************ LOCK
            if on:
                self.busy_threads -= 1
                on = False
            while len(self.request_list) > 0:
                self.request_cond.wait()
            mdroid = self.request_list.pop(0)
            self.busy_threads += 1
            on = True
            self.request_cond.release() #************ UNLOCK

            deploy_measurement(mdroid)


    def listener(self):
        on = False
        while self.keep_going:
            self.listen_cond.acquire() #************ LOCK
            if on:
                self.busy_threads -= 1
            while len(self.request_list) > 0:
                self.listen_cond.wait()
            mdroid = self.listen_list.pop(0)
            self.busy_threads += 1
            on = True
            self.listen_cond.release() #************ UNLOCK

            sp = mdroid.get_stream_params()
            atlas_stream = AtlasStream()
            atlas_stream.connect()
            channel = "result"
            atlas_stream.bind_channel(channel, mdroid.response_handler)
            stream_parameters = sp #{"msm":ld['m']}
            atlas_stream.start_stream(stream_type="result", **stream_parameters)
            atlas_stream.timeout(seconds=10)
            atlas_stream.disconnect()
