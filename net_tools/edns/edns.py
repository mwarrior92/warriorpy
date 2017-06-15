#!/usr/bin/env python

# Most of this is a modified version of  Florian Streibelt's modified OpenDNS
# code. This code should not be public!
#

import socket
import struct
import sys
import dns
import dns.edns
import dns.flags
import dns.message
import dns.query

import logging

logger = logging.getLogger(__name__)

class ednsException(Exception):
    pass


class ClientSubnetOption(dns.edns.Option):
    """Implementation of draft-vandergaast-edns-client-subnet-01.

        Attributes:
            family: An integer inidicating which address family is being sent
            ip: IP address in integer notation
            mask: An integer representing the number of relevant bits being sent
            scope: An integer representing the number of significant bits used by
            the authoritative server.
    """

    def __init__(self, family, ip, bits=24, scope=0):
        super(ClientSubnetOption, self).__init__(0x0008)

        if not (family == 1 or family == 2):
            raise ednsException("Family must be either 1 (IPv4) or 2 (IPv6)")

        self.family = family
        self.ip = ip
        self.mask = bits
        self.scope = scope

        if self.family == 1 and self.mask > 32:
            raise ednsException("32 bits is the max for IPv4 (%d)" % bits)
        if self.family == 2 and self.mask > 128:
            raise ednsException("128 bits is the max for IPv6 (%d)" % bits)

    def calculate_ip(self):
        """Calculates the relevant ip address based on the network mask.

            Calculates the relevant bits of the IP address based on network mask.
            Sizes up to the nearest octet for use with wire format.

            Returns:
            An integer of only the significant bits sized up to the nearest
            octect.
            """

        if self.family == 1:
            bits = 32
        elif self.family == 2:
            bits = 128

        ip = self.ip >> bits - self.mask

        if (self.mask % 8 != 0):
            ip = ip << 8 - (self.mask % 8)

        return ip

    def to_wire(self, file):
        """Create EDNS packet as definied in draft-vandergaast-edns-client-subnet-01."""

        # TODO: I think this still uses the old experimental values, need to
        # update

        ip = self.calculate_ip()

        mask_bits = self.mask
        if mask_bits % 8 != 0:
            mask_bits += 8 - (self.mask % 8)

        if self.family == 1:
            test = struct.pack("!L", ip)
        test = test[-(mask_bits / 8):]
        #elif self.family == 2:
        #    test = struct.pack("!QQ", ip >> 64, ip & (2 ** 64 - 1))
        #    test = test[-(mask_bits / 8):]

        format = "!HBB%ds" % (mask_bits / 8)
        data = struct.pack(format, self.family, self.mask, 0, test)

        file.write(data)

    def from_wire(cls, otype, wire, current, olen):
        """Read EDNS packet as defined in draft-vandergaast-edns-client-subnet-01.

        Returns:
            An instance of ClientSubnetOption based on the ENDS packet
        """

        data = wire[current:current + olen]
        (family, mask, scope) = struct.unpack("!HBB", data[:4])

        c_mask = mask
        if mask % 8 != 0:
            c_mask += 8 - (mask % 8)

        ip = struct.unpack_from("!%ds" % (c_mask / 8), data, 4)[0]

        if (family == 1):
            ip = struct.unpack("!L", ip + '\0' * ((32 - c_mask) / 8))[0]
        elif (family == 2):
            hi, lo = struct.unpack("!QQ", ip + '\0' * ((128 - c_mask) / 8))
            ip = hi << 64 | lo
        else:
            raise ednsException("Returned a family other then 1 (IPv4) or 2 (IPv6)")
        return cls(family, ip, mask, scope)

    from_wire = classmethod(from_wire)

    def __eq__(self, other):
        """Rich comparison method for equality.

            Two ClientSubnetOptions are equal if their relevant ip bits, mask, and
            family are identical. We ignore scope since generally we want to
            compare questions to responses and that bit is only relevant when
            determining caching behavior.

            Returns:
            boolean
        """

        if not isinstance(other, ClientSubnetOption):
            return False
        if self.calculate_ip() != other.calculate_ip():
            return False
        if self.mask != other.mask:
            return False
        if self.family != other.family:
            return False

        return True

    def __ne__(self, other):
        """Rich comparison method for inequality.

            See notes for __eq__()

            Returns:
            boolean
        """
        return not self.__eq__(other)

def do_edns_c_query(resolver,ip,family,mask,query, timeout=1.0):

    # ip - client_ip to fake
    # family - IP-family (int)
    # mask - mask to send (int)
    # query - name to query

    dns.edns._type_to_class[0x0008] = ClientSubnetOption

    #client_ip_str=socket.inet_ntoa(struct.pack('!L',ip))
    #lprefix = "%s %s %s %d -" % (resolver,query,client_ip_str,mask)
    lprefix=ip

    cso = ClientSubnetOption(family, ip, mask)
    message = dns.message.make_query(query, "A")
    message.use_edns(options=[cso])


    # NOTE: THis is not forgiving! No TCP fallback!
    #try:

    r = dns.query.udp(message, resolver,timeout=timeout)


    if r.flags & dns.flags.TC:
        logger.debug( "D: %s udp flag TC, trying tcp" % lprefix )
        try:
            r = dns.query.tcp(message, resolver)
            #UTO - TCPOK
        except socket.error:
            logger.error( "E: %s tcp refused after TC flag set" % lprefix )
            raise ednsException("tcp refused after TC flag set")

    #    #else:
    #        # UDPOK
    #except dns.exception.Timeout:
    #    logger.debug( "D: %s udp timeout, trying tcp" % lprefix )
    #    try:
    #        r = dns.query.tcp(message, resolver)
    #        # TCPON
    #    except socket.error:
    #        logger.error( "E: %s tcp refused too" % lprefix )
    #        raise ednsException("tcp refused after udp timeout")


    records=[]
    for answers in r.answer:
        for item in answers.items:
            # there seems no generic way to get the payload, except using to_text
            # but that does not include the type of RR (e.g. CNAME)
            records.append( "%s %s %s" % (item.rdclass,item.rdtype,item.to_text() ) )

    response={}

    have_csn = False
    for options in r.options:
        if isinstance(options, ClientSubnetOption):
            have_csn=True
            response['client_ip']     = cso.ip
            response['client_family'] = cso.family
            response['client_mask']   = cso.mask
            response['client_scope']  = options.scope

    if not have_csn:
        logger.error( "E: %s clientsubnet: FALSE" % lprefix )
        raise ednsException("No csn option")

    #logger.debug (  "D: %s %s" % ( lprefix, str(r).splitlines() ) )
    response['rcode'] = r.rcode()
    response['dns_results'] = r
    response['records'] = records
    return response

def do_query(resolver, query, origin, mask, timeout=1.0):
    """ A wrapper that will cleanly parse text input """
    # Parse out the IP, turns it into an int
    ip = struct.unpack('!L', socket.inet_aton(origin))[0]


    # Resolver and query stay strings, forces ipv4
    resp = do_edns_c_query(resolver, ip, 1, mask, query, timeout)

    return resp

if __name__ == "__main__":
    if len(sys.argv) <= 2:
        print("Format is %s [nameserver] [record] ([ip_to_fake [mask]])" % sys.argv[0])
        sys.exit(1)

    if len(sys.argv) >= 4:
        if ":" in sys.argv[3]:
            family = 2
            hi, lo = struct.unpack('!QQ', socket.inet_pton(socket.AF_INET6, sys.argv[3]))
            ip = hi << 64 | lo
        elif "." in sys.argv[3]:
            family = 1
            ip = struct.unpack('!L', socket.inet_aton(sys.argv[3]))[0]
        else:
            print "'%s' doesn't look like an IP to me..." % sys.argv[3]
            sys.exit(1)
    else:
        family = 1
        ip = 0xC0000200

    if len(sys.argv) == 5:
        mask = int(sys.argv[4])
    else:
        if family == 2:
            mask = 48
        else:
            mask = 24

    resolver = sys.argv[1]
    query = sys.argv[2]

    print "using resolver %s and client ip %s with mask %s to query %s" % (resolver,ip,mask,query)
    x=do_edns_c_query(resolver,ip,family,mask,query)
    print "OUTPUT:"
    print x
