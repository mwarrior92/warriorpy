import ipwhois.asn_fetch as af
import warriorpy.shorthand.diriofile as df
import warriorpy.shorthand.linefile as lf
from collections import defaultdict

def checkcache(itemname, filename='importvars/asn.cache', incachedir='importvars/mycache'):
    ''' checks cached asns; else, does a new query and stores result in cache'''
    retval = '?'
    cachedir = df.rightdir(df.getdir(__file__)+incachedir)
    if len(itemname) >= 7 and '.' in itemname:
        tmpfname = cachedir+itemname.split('.')[0]+'.cache'
        data = defaultdict(str, df.pjsonin(tmpfname))
        tmpval = data[itemname]
        if df.isint(tmpval) or tmpval == 'NA':
            retval = tmpval
        elif tmpval == str():
            asn = None
            try:
                asn = af.asn_lookup(itemname)
            except:
                pass
            if asn is None:
                data[itemname] = '?'
            else:
                data[itemname] = asn
                retval = asn
            df.pjsonout(tmpfname, dict(data), 'w')
    return retval
