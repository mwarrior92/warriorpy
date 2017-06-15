import warriorpy.shorthand.roach as roach
import socket
import time
import random
import struct
import select
import warriorpy.shorthand.easyshell as es
import urllib2

def get_my_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('google.com',0))
    return s.getsockname()[0]

def get_my_name(myip=None):
    try:
        if myip is None:
            return socket.gethostbyaddr(get_my_ip())
        else:
            return socket.gethostbyaddr(myip)
    except socket.error as bla:
        roach.error(str(bla))
        return "*"

class TimeoutError(BaseException):
    pass

def thandler(signum, frame):
    #timeout handler
    raise TimeoutError('timeout')

def traceroute(dest_addr):
    port = 33434
    max_hops = 30
    icmp = socket.getprotobyname('icmp')
    udp = socket.getprotobyname('udp')
    ttl = 1
    hops = list()
    while True:
        curr_addr = None
        curr_name = None
        try:
            recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
            recv_socket.settimeout(5)
            send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, udp)
            send_socket.settimeout(5)
            send_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
            recv_socket.bind(("", port))
            send_socket.sendto("", (dest_addr, port))
            try:
                _, curr_addr = recv_socket.recvfrom(512)
                curr_addr = curr_addr[0]
                try:
                    curr_name = socket.gethostbyaddr(curr_addr)[0]
                except socket.error:
                    curr_name = curr_addr
            except socket.error:
                pass
            finally:
                send_socket.close()
                recv_socket.close()
        except socket.timeout:
            pass

        if curr_addr is not None:
            curr_host = (curr_name, curr_addr)
        else:
            curr_host = ('*','*')
        print(curr_host)
        hops.append(curr_host)

        ttl += 1
        if curr_addr == dest_addr or ttl > max_hops:
            break
    return hops

def chk(data):
    x = sum(x << 8 if i % 2 else x for i, x in enumerate(data)) & 0xFFFFFFFF
    x = (x >> 16) + (x & 0xFFFF)
    x = (x >> 16) + (x & 0xFFFF)
    return struct.pack('<H', ~x & 0xFFFF)

def ping(addr):
    # sends a single ping to specified url using terminal
    # command 'ping'. Returns tuple of 4 values:
    # RTT (float), RTT time unit (str), ping size (str),
    # url ip (str)
    res = es.terminal(['ping', '-c', '1', addr])
    res = res.split('\n')[1]
    chunks = res.split(' ')
    size = chunks[0]
    if '(' in res:
        src = chunks[4]
        src = src.replace('(','')
        src = src.replace(')','')
    else:
        src = chunks[3]
    chunks = res.split('time=')
    chunks= chunks[1].split(' ')
    t = float(chunks[0])
    unit = chunks[1]
    return (t, unit, size, src)

def sendstr(dst_dom, dst_port, data):
    if ':' in dst_dom:
        req = urllib2.Request(dst_dom+':'+dst_port, data)
    else:
        req = urllib2.Request('http://'+dst_dom+':'+dst_port, data)
    res = urllib2.urlopen(req, timeout=5)

'''
def socket_ping(addr, timeout=1, number=1, data=b''):
    # - must be sudo
    # - doesn't use terminal
    try:
        conn = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        try:
            payload = struct.pack('!HH', random.randrange(0, 65536), number) + data

            conn.connect((addr, 80))
            conn.sendall(b'\x08\0' + chk(b'\x08\0\0\0' + payload) + payload)
            start = time.time()

            while select.select([conn], [], [], max(0, start + timeout - time.time()))[0]:
                data = conn.recv(65536)
                if len(data) < 20 or len(data) < struct.unpack_from('!xxH', data)[0]:
                    continue
                if data[20:] == b'\0\0' + chk(b'\0\0\0\0' + payload) + payload:
                    return time.time() - start
        finally:
            conn.close()
    except Exception as bla:
        roach.error("netquery.socket_ping error: "+bla)
'''

