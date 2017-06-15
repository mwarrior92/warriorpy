import bisect

class rangeQuery:

    def __init__(self, ranges):
        self.startsMap = {}
        self.starts = []

        for start, end in ranges:
            if start not in self.startsMap:
                self.startsMap[start] = []
                self.starts += [start]
            self.startsMap[start] += [end]
        
        self.starts.sort()
    
    def getBestFit(self, val, val2=None):
        # support queries for a range of values
        if val2 is None:
            val2 = val
        else:
            val, val2 = min(val, val2), max(val, val2)

        # get a list of possible range start values, in descending order
        # get the index of the largest start value that's <= val
        toUse = bisect.bisect(self.starts, val)

        if toUse == 0:
            # no ranges match...
            return None
        
        # now, go through the ranges for these start values...
        possibleStarts = self.starts[:toUse]
        possibleStarts.reverse()

        # select the smallest matching range
        # once we get too far away...we can terminate the search because we
        # know that any match will have to have a range size of at least X
        smallestSize = None
        bestStartEnd = None
        for start in possibleStarts:
            if smallestSize is not None and smallestSize < val - start:
                # we can't find a better fit.
                break
            
            ends = self.startsMap[start]
            for end in ends:
                # JSO: modified to use val2, which is typically
                #      the same as val, except when doing range queries
                if val2 <= end:
                    size = end - start
                    if smallestSize is None or size < smallestSize:
                        smallestSize = size
                        bestStartEnd = (start, end)
        
        return bestStartEnd

class ip:
    """
    Simple adapter for range queries to use pairs of IP addresses or IP prefixes.

    Checks to be sure that only one version of IP (4 or 6) is used at a time.
    """

    def __init__(self, ranges):
        from IPy import IP

        self.version = None
        self.key_map = {}

        # translate ranges given as IP addresses/prefixes to integers
        these_ranges = []
        for entry in ranges:
            if type(entry) == list or type(entry) == tuple:
                lo, hi = entry

                lo = IP(lo)
                hi = IP(hi)

                if self.version is None:
                    self.version = lo.version()

                if lo.version() != self.version:
                    raise RuntimeError("IP version mismatch")
                
                if hi.version() != self.version:
                    raise RuntimeError("IP version mismatch")

                lo_ip = lo.int()
                hi_ip = hi.int()
            
            else:
                # must be a prefix -- single entry
                ip = IP(entry)
                if self.version is None:
                    self.version = ip.version()

                if self.version != ip.version():
                    raise RuntimeError("IP version mismatch")

                lo_ip = ip[0].int()
                hi_ip = ip[-1].int()

            self.key_map[ (lo_ip, hi_ip) ] = entry

            these_ranges.append( (lo_ip, hi_ip) )

        self.rq = rangeQuery(these_ranges)

    def getBestFit(self, val, val2=None):
        from IPy import IP

        # support queries for a range of values
        if val2 is None:
            val2 = val
        else:
            val, val2 = min(val, val2), max(val, val2)

        val = IP(val).int()
        val2 = IP(val2).int()

        res = self.rq.getBestFit(val, val2)

        return self.key_map.get(res, None)

if __name__ == "__main__":
    # for testing purposes
    ranges = [
        (1,100),
        (2,5),
        (2,2),
        (1,10),
        (1,50),
    ]

    for val in ranges:
        print val
    print

    rq = rangeQuery(ranges)

    def test(val):
        res = rq.getBestFit(val)
        print val, res

    def test2(val, val2):
        res = rq.getBestFit(val, val2)
        print val, val2, res

    test(2)
    test(3)
    test(5)
    test2(2,6)
    test2(2,10)

