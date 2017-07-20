from netaddr import IPNetwork as CIDR
from netaddr import IPAddress as IP
from IPy import IP as IP2
import socket
import struct
from numbers import Number

def is_local(ip):
    '''
        is ip is in local block?
    '''
    if IP(ip) in CIDR("172.16.0.0/12") or IP(ip) in CIDR("10.0.0.0/8") \
            or IP(ip) in CIDR("192.168.0.0/16"):
        return True
    else:
        return False


def is_public(ip):
    if type(ip) is int:
        ip = int2ip(ip)
    return IP2(ip+"/32").iptype() == "PUBLIC"


def ip2int(addr):
    return struct.unpack("!I", socket.inet_aton(addr))[0]


def int2ip(addr):
    return socket.inet_ntoa(struct.pack("!I", addr))


def make_v4_prefix_mask(masklen):
    maskval = 2**32 - 1
    maskval = maskval>>(32-masklen)
    maskval = maskval<<(32-masklen)
    return maskval


prefix_cache = dict()

def prefix_match(ip1, ip2):
    if not isinstance(ip1, Number):
        ip1 = ip2int(ip1)
    if not isinstance(ip2, Number):
        ip2 = ip2int(ip2)

    tmp = tuple(sorted([ip1, ip2]))
    if tmp in prefix_cache:
        return prefix_cache[tmp]

    xor = bin(ip1 ^ ip2)
    bitcount = len(xor) - 2
    prefix_cache[tmp] = bitcount
    return bitcount
