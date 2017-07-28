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

def fix_ownership(path):
    # Change the owner of the file to SUDO_UID
    uid = os.environ.get('SUDO_UID')
    gid = os.environ.get('SUDO_GID')
    if uid is not None:
        os.chown(path, int(uid), int(gid))
        logger.debug("updated ownership of "+path)

def get_file(path, mode="a+"):
    """Create a file if it does not exists, fix ownership and return it open"""
    # first, create the file and close it immediatly
    if 'r' not in mode:
        open(path, 'a').close()

    # then fix the ownership
    fix_ownership(path)

    # open the file and return it
    return open(path, mode)

def write(pathtofile, content):
    # writes to file. Will append if file exists. Note that this is just doing
    # ascii... nothing fancy
    try:
        f = get_file(pathtofile, 'a+')
        try:
            f.write(content)
        finally:
            f.close()
    except IOError:
        logger.error("failed to write "+pathtofile)
    logger.debug("appended to "+pathtofile)

def append(pathtofile, content):
    # wrapper for write (in case "append" is a more intuitive terminology)
    write(pathtofile, content)

def appendline(pathtofile, content):
    # wrapper for write (in case "append" is a more intuitive terminology)
    write(pathtofile, '\n'+content)

def overwrite(pathtofile, content):
    # writes to file. Will overwrite if file exists
    try:
        f = get_file(pathtofile, 'w+')
        try:
            f.write(content)
        finally:
            f.close()
    except IOError:
        logger.error('IOError overwriting to '+pathtofile)
    logger.debug("wrote over "+pathtofile)

def isfile(fname):
    # wrapper for checking to see if a file fname exists
    return os.path.isfile(fname)

def rightdir(path):
    # this makes sure that the entire path tree of interest exists
    # by iterating through the path tree and creating missing directories.
    # In other words, it makes everything "right" (correct)
    dirs = path.split('/')
    path = '/'
    if dirs[0] != "":
        raise ValueError('relative path not allowed')
    for d in dirs:
        # account for empty strings from split
        if d == '..':
            path = '/'.join(path.split('/')[:-2])+'/'
        elif d != '':
            path = path + d + '/'
        else:
            continue
        try:
            if not os.path.exists(path):
                os.makedirs(path)
                fix_ownership(path)
        except OSError:
            logger.error('OSError creating file path for '+path)
    fix_ownership(path)
    logger.debug("corrected path: "+path)
    return path

def getdir(pyfile=__file__):
    # return the string of path to current script file
    return os.path.dirname(os.path.realpath(pyfile))+'/'


def listfiles(parentdir, fullpath=False, prefix="", containing=""):
    # return list of file names in parentdir;
    # setting fullpath to True will give filenames with the direct/full path as
    # a prefix
    if fullpath:
        for root, dirs, files in os.walk(parentdir):
            outlist = list()
            for f in files:
                if prefix == "" and containing == "":
                    outlist.append(rightdir(parentdir)+f)
                elif prefix == "":
                    if containing in f:
                        outlist.append(rightdir(parentdir)+f)
                elif containing == "":
                    if f.startswith(prefix):
                        outlist.append(rightdir(parentdir)+f)
                elif f.startswith(prefix) and contains in f:
                    outlist.append(rightdir(parentdir)+f)

            return outlist
    else:
        for root, dirs, files in os.walk(parentdir):
            return files

def listfilepaths(parentdir):
    # Wrapper for listfiles; sets fullpath to True (see listfiles)
    return listfiles(parentdir, True)


def listdirs(parentdir, fullpath=False):
    # return list of child dir names in parentdir
    # setting fullpath to True will give dirnames with the direct/full path as
    # a prefix
    if fullpath:
        outlist = list()
        for root, dirs, files in os.walk(parentdir):
            for d in dirs:
                outlist.append(rightdir(parentdir)+d)
            return outlist
    else:
        for root, dirs, files in os.walk(parentdir):
            return dirs

def listdirpaths(parentdir):
    # Wrapper for listdirs; sets fullpath to True (see listdirs)
    return listdirs(parentdir, True)

def remove(fname):
    # delete file fname
    try:
        if fname[-1] == '*' or fname[-1] == '/':
            shutil.rmtree(fname)
        else:
            os.remove(fname)
    except OSError:
        logger.error('OSError removing '+fname)
    logger.debug("removed "+fname)

def copy(src, dst):
    # copy file src to file or dir dst
    try:
        if src[-1] == '/':
            shutil.copytree(src, dst, symlinks=True)
        else:
            shutil.copy(src, dst)
    except OSError:
        logger.error('OSError copying '+src+' to '+dst)
    logger.debug("copied "+src+" to "+dst)

def getleaf(fpath, period=True):
    # get string of last block of path
    tmpl = fpath.split('/')
    if tmpl[-1] == '':
        leaf = tmpl[-2]
    else:
        leaf = tmpl[-1]
    if '.' in leaf and period:
        # removes file extension
        return ''.join(leaf.split('.')[:-1])
    else:
        return leaf

##################################################################
#          FILE & TEXT PARSING & FORMATTING
##################################################################

def untar(fname, dst):
    tar = tarfile.open(fname)
    tar.extractall(path=dst)
    tar.close()
    fix_ownership(dst)

def make_tarfile(output_filename, source_dir):
    try:
        tar = tarfile.open(output_filename, "w:gz")
        try:
            tar.add(source_dir, arcname=os.path.basename(source_dir))
        except:
            logger.error("failed to make "+output_filename+" from "+source_dir)
    except IOError:
        logger.error("IOError: failed to make "+output_filename+" from "+source_dir)
    finally:
        tar.close()
    try:
        fix_ownership(output_filename)
    except:
        pass
    logger.debug("made tar ball named "+output_filename)

def load(pathtofile):
    outstr = ''
    try:
        f = get_file(pathtofile, 'r')
        try:
            outstr = f.read().strip()
        finally:
            f.close()
    except IOError:
        logger.error("failed to write "+pathtofile)
    return outstr

def getlines(filename):
    # read all lines from a file; return as array of strings
    lines = list()
    txt = 'tmp'
    try:
        f = get_file(filename, 'r+')
        try:
            while txt != '':
                txt = str(f.readline())
                if txt.strip() != '':
                    lines.append(txt.strip())
        finally:
            f.close()
    except IOError:
        logger.error('IOError getting lines from '+filename)
    logger.debug("read from "+filename)
    return lines

def jsonout(pathtofile, data, writetype='a+'):
    try:
        f = get_file(pathtofile, writetype)
        try:
            json.dump(data, f)
            f.write("\n")
        finally:
            f.close()
    except (IOError, OSError):
        logger.error("failed to write "+pathtofile)
    logger.debug("wrote to "+pathtofile)

def jsonin(pathtofile):
    data = {}
    try:
        f = get_file(pathtofile, 'r+')
        try:
            data = byteify(json.load(f))
        finally:
            f.close()
    except (IOError, OSError, EOFError, ValueError):
        logger.error("failed to read "+pathtofile)
        pass
    logger.debug("read from "+pathtofile)

    return data

def json2ddict(funclist, jdict):
    jdict = ddict(funclist[0], jdict)
    if len(funclist) > 1:
        for item in jdict:
            jdict[item] = json2ddict(funclist[1:], jdict[item])

    return jdict


def jsonlistin(pathtofile):
    lines = getlines(pathtofile)
    for ind, line in enumerate(lines):
        lines[ind] = byteify(json.loads(line))
    logger.debug("read from "+pathtofile)
    return lines

def pjsonout(pathtofile, data, writetype='w'):
    try:
        f = get_file(pathtofile, writetype)
        try:
            pickle.dump(data, f)
            f.write("\n")
        finally:
            f.close()
    except (IOError, OSError):
        logger.error("failed to write "+pathtofile)
    logger.debug("wrote to "+pathtofile)

def pjsonin(pathtofile):
    data = {}
    try:
        f = get_file(pathtofile, 'r+')
        try:
            data = byteify(pickle.load(f))
        finally:
            f.close()
    except (IOError, EOFError, OSError, ValueError):
        logger.error("failed to read "+pathtofile)
    logger.debug("read from "+pathtofile)

    return data

def picklein(pathtofile):
    data = None
    try:
        f = get_file(pathtofile, 'r+')
        try:
            data = pickle.load(f)
        finally:
            f.close()
    except (IOError, EOFError, OSError, ValueError):
        logger.error("failed to read "+pathtofile)
    logger.debug("read from "+pathtofile)

    return data

def pickleout(pathtofile, content):
    data = None
    try:
        f = get_file(pathtofile, 'w+')
        try:
            data = pickle.dump(content, f)
        finally:
            f.close()
    except (IOError, EOFError, OSError, ValueError):
        logger.error("failed to read "+pathtofile)
    logger.debug("read from "+pathtofile)

    return data


def pjsonlistin(pathtofile):
    lines = getlines(pathtofile)
    for ind, line in enumerate(lines):
        lines[ind] = byteify(pickle.loads(line))
    logger.debug("read from "+pathtofile)
    return lines

def txt2num(txt):
    # convert string to number (float if "." in text, else int) if possible
    try:
        if '.' in txt:
            return float(txt)
        else:
            return int(txt, 0)
    except ValueError:
        # text is not correct format for conversion
        return txt

def line2list(line_in, d=',', atoi=False):
    # convert a string delimited by d into a list; if atoi is True, this
    # will attempt to convert numeric values into floats/ints (see text2num)
    tmplist = line_in
    if d in line_in:
        tmplist = tmplist.split(d)
        if atoi:
            for ind, item in enumerate(tmplist):
                tmplist[ind] = txt2num(item)
    return tmplist

def list2line(t, d=','):
    # convert list into string delimited by d
    t_str = ''
    for item in t:
        t_str += str(item)+d
    return t_str[0:-1]

def list2col(lst):
    # change list into vertical text list,
    # where each line is a list element; if a line contains an iterable type,
    # that is converted into a string using list2line
    txt = ''
    for item in lst:
        if type(item) is tuple \
                or type(item) is list \
                or type(item) is set:
            tmpstr = list2line(item)
        else:
            tmpstr = str(item)
        txt += tmpstr+'\n'
    return txt[0:-1]

def col2list(lines, d=',', stayString=False):
    # convert vertical list of items (from file) into python lists; if a line
    # contains a list delimited by d, this is also converted into a list
    outlist = []
    for line in lines:
        outlist.append(line2list(line, d, stayString))
    return outlist

def byteify(var):
    # get rid of the random unicode stuff in json strings read from files
    if isinstance(var, dict):
        return dict([(byteify(key), byteify(value)) for key, value in var.iteritems()])
    elif isinstance(var, list):
        return [byteify(element) for element in var]
    elif isinstance(var, unicode):
        return var.encode('utf-8')
    else:
        return var

def tmpname():
    # return a time based randomly generated string
    return ''.join(str(time.time()).split('.'))

def isint(val):
    try:
        tmp = int(val)
        return True
    except ValueError:
        return False

def bsoup(src):
    # basically just a wrapper for BeautifulSoup because it's such a big word
    soup = BeautifulSoup(src, "html.parser")
    return soup

class looplist(list):
    # extension for lists to be modulo indexed
    def __getitem__(self, item):
        list_len = len(self)
        m_item = item % list_len
        tmp_list = list(self)
        return tmp_list[m_item]


def tuplize(l):
    if not hasattr(l, '__iter__'):
        l = [l]
    s = sorted(l)
    return tuple(s)


def make_hashable(o):
    if any([type(o) is z for z in [dict, ddict]]):
        for k in o:
            o[k] = make_hashable(o[k])
        return dict(o)
    elif any([type(o) is z for z in [list, tuple, set]]):
        l = list()
        for item in o:
            l.append(make_hashable(item))
        return tuple(l)
    else:
        return o
