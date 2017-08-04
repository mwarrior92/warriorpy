"""
dns_tools.py - A collection of various DNS tools.

    reverse_dns_lookip(server_ip) - takes the IP address as a string, returns
    the reverse dns result as a string or raises an error

"""


import IPy
import dns.resolver, dns.message, dns.rdatatype
from ipwhois import IPWhois

##################################################################
#                           LOGGING
##################################################################
import logging
import logging.config

logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

# create logger
logger = logging.getLogger(__name__)
logger.debug(__name__+"logger loaded")



resolver = dns.resolver.Resolver()
resolver.lifetime = 1
resolver.timeout = 1

def reverse_dns_lookup(server_ip):
    """ Perform a reverse DNS lookup of the dns server in question.

    Cache results to file to reduce the number of lookups that we
    actually need to do """

    # Let's bring it into the real format
    addr = IPy.IP(server_ip)
    query = addr.reverseName()
    resp = None

    # Do all the seolver voodoo from John Otto
    try:
        resp = resolver.query(query, rdtype=dns.rdatatype.PTR)
    except Exception as e:
        if type(e) != dns.resolver.NXDOMAIN:
            try:
                resp = resolver.query(query, rdtype=dns.rdatatype.PTR)
            except Exception as e:
                raise e

    # Figure out what type of response it was, parse accordingly
    if resp:
        if resp.rrset.rdtype == dns.rdatatype.SOA:
            name = "SOA", str(resp.rrset[0].mname)
        elif resp.rrset.rdtype == dns.rdatatype.PTR:
            name = str(resp.rrset[0].target)

    return name


def get_owner_name(server_ip, res=None):
    '''
    provide server IP in string format
    returns NAME ({'network': 'name': NAME}) from result answer
    '''
    try:
        if res is None:
            if IPy.IP(server_ip+"/32").iptype() == "PUBLIC":
                tmp = IPWhois(server_ip)
                res = tmp.lookup_rdap(depth=1)
                return res['network']['name']
        else:
            return res['network']['name']
    except Exception as e:
        logger.debug(str(e))
    return None


def get_cidr(server_ip, res=None):
    try:
        if res is None:
            if IPy.IP(server_ip+"/32").iptype() == "PUBLIC":
                tmp = IPWhois(server_ip)
                res = tmp.lookup_rdap(depth=1)
                return res['network']['cidr']
        else:
            return res['network']['cidr']
    except Exception as e:
        logger.debug(str(e))
    return None
