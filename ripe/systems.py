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


def deploy_measurement(request, mdroid):
    is_success, measids = ra.send_request(request)
    if is_success:
        mdroid.success_handler(measids)
        for m in measids:
            mdroid.push_listener(m)
    else:
        mdroid.fail_handler(request)


def listener(ld):
    atlas_stream = AtlasStream()
    atlas_stream.connect()
    channel = "result"
    atlas_stream.bind_channel(channel, ld['mdroid'].response_handler)
    stream_parameters = {"msm":ld['m']}
    atlas_stream.start_stream(stream_type="result", **stream_parameters)
    atlas_stream.timeout(seconds=10)
    atlas_stream.disconnect()


def make_test(d):
    if 'traceroute' in d:
        return ra.make_traceroute_test(d['traceroute'])
    elif 'ping' in d:
        return ra.make_ping_test(d['ping'])
    elif 'dns' in d:
        return ra.make_dns_test(d['dns'])
    else:
        logger.error("incorrect usage of 'make_test': should be traceroute,
            ping, or dns test")


class measurement_droid:
    def __init__(self, mseq, tman):
        self.mseq = mseq # message_sequence
        self.tman = tman # thread_manager
        self.result_sets = list()

        func = self.mseq.get_first_step()
        request = func()
        self.push_request(request)


    def success_handler(self, measids):
        self.mseq.started(measids)


    def fail_handler(self, req):
        pass

    def push_request(self, r):
        self.tman.push_request({'request':r, 'mdroid':self})


    def push_listener(self, m):
        self.tman.push_listener({'m':m, 'mdroid':self})


    def response_handler(self, resp):
        measid = resp['measid']
        step, arg = self.mseq.finished(measid, resp)
        if arg is not None:
            self.result_lists.append(arg)
        func = self.mseq.get_action(step)
        request = func(arg)
        if request is not None:
            self.push_request(request)


def do_nothing(arg):
    return None


class measurement_sequence:
    def __init__(self, seq):
        self.seq = seq # function list; should end with do_nothing
        self.next_step = dict()
        self.completed = dict()
        self.results = defaultdict(list)
        self.my_lock = threading.Lock()


    def get_first_step(self):
        return self.seq[0]


    def started(self, m, step):
        t = df.tuplize(m)
        self.step[t] = step
        for m in t:
            self.completed[m] = False


    def finished(self, m, result):
        self.completed[m] = True
        for s in self.step:
            if m in s:
                self.results[s].append(result)
                if len([c for c in s if self.completed[c]]) == len(s):
                    for c in s:
                        del self.completed[c]
                        return self.step[s]+1, results[s] # do something
                    else:
                        break
            return -1, None # do nothing


    def get_action(self, step=0):
        return self.seq[step]


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
        self.request_pool = request_pool
        self.max_threads = max_threads
        self.keep_going = True
        self.listen = threading.Condition()
        self.listener_list = list()
        self.lock = threading.Condition()

        thread = threading.Thread(target=self.stir)
        thread.daemon = True
        thread.start()


    def push_request(self, rd):
        self.lock.acquire()
        if threading.active_count() < self.max_threads():
            self.request_pool.lock()
            self.request_pool.push(rd)
            self.request_pool.unlock()
            thread = threading.Thread(target=worker, args=[self.request_pool])
            thread.daemon = True
            thread.start()
        self.lock.release()


    def push_listener(self, ld):
        if threading.active_count() < self.max_threads():
            thread = threading.Thread(target=listener, args=[ld])
            thread.daemon = True
            thread.start()
        else:
            self.listen.acquire()
            self.listener_list.append(ld)
            self.listen.release()


    def stir_pools(self):
        self.lock.acquire()
        self.lock.notify()
        self.lock.release()


    def stop_stirring(self):
        self.keep_going = False


    def stir(self):
        # this gets notified by stir_pools whenever a thread finishes;
        # it tries to make new threads to handle any outstanding items
        self.lock.acquire()
        while self.keep_going:
            if threading.active_count() < self.max_threads:
                ld = None
                self.listen.acquire()
                if len(self.listener_list) > 0:
                    ld = self.listener_list.pop(0)
                self.listen.release()
                if ld is not None:
                    self.push_listener(ld)

                rd = None
                self.request_pool.lock()
                if len(self.request_pool) > 0:
                    thread = threading.Thread(target=worker, args=[self.request_pool])
                    thread.daemon = True
                    thread.start()
            self.lock.wait()
            time.sleep(1)
        self.lock.release()



