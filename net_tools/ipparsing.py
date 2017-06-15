from netaddr import IPNetwork as CIDR
from netaddr import IPAddress as IP
import socket
import struct

def is_local(ip):
    '''
        is ip is in local block?
    '''
    if IP(ip) in CIDR("172.16.0.0/12") or IP(ip) in CIDR("10.0.0.0/8") \
            or IP(ip) in CIDR("192.168.0.0/16"):
        return True
    else:
        return False


def ip2int(addr):
    return struct.unpack("!I", socket.inet_aton(addr))[0]


def int2ip(addr):
    return socket.inet_ntoa(struct.pack("!I", addr))

