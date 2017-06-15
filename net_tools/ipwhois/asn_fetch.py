import ipwhois
import sys

def asn_lookup(ip_string):

    obj = ipwhois.IPWhois(ip_string, 1)
    result = obj.lookup()

    return result['asn']

if __name__ == "__main__":
    print asn_lookup(sys.argv[1])
