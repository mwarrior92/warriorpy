# list_tools.py - Some general tools for manipulating lists that seemed general
# enough to put over here

def chunks(l,n):
    """Splits list l into n-sized chunks"""
    for i in xrange(0, len(l), n):
        yield l[i:i+n]
