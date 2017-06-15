import socket
from collections import defaultdict
import ripe.atlas.cousteau as rac
from datetime import datetime
from warriorpy.net_tools import asncache
from warriorpy.shorthand import diriofile as df
import logging
import logging.config

##################################################################
#                           LOGGING
##################################################################

logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

# create logger
logger = logging.getLogger(__name__)
logger.debug(__name__+"logger loaded")


my_key = "b9ec2897-dba8-4f35-baa9-aeb1b6e4f9d1"
kill_key = "7374858f-da89-4758-9e20-8bde940ad828"


def make_ping_test(dstips):
    """
    :param dstips: list
    :return: list
    """
    pinglist = list()
    for dstip in dstips:
        pinglist.append(
            rac.Ping(
                af=4,
                target=dstip,
                description="Ping Test"
            )
        )
    return pinglist


def make_traceroute_test(dstips, packets=1):
    """
    :param dstips: list
    :return: list
    """
    trlist = list()
    for dstip in dstips:
        trlist.append(
            rac.Traceroute(
                af=4,
                target=dstip,
                description="Traceroute Test",
                protocol="ICMP",
                packets=packets
            )
        )
    return trlist


def get_probes(country=None, extra_tags="", ip_version=4):
    """
    :param country: string
    :param extra_tags: string
    :param ip_version: int
    :return: dict
    """
    if country is not None:
        if len(extra_tags) > 0:
            filters = {"tags": "system-ipv"+str(ip_version)+"-works"+","+extra_tags,
                       "country_code": country, "status_name": "Connected", "is_public": True}
        else:
            filters = {"tags": "system-ipv" + str(ip_version) + "-works",
                       "country_code": country, "status_name": "Connected", "is_public": True}
    else:
        if len(extra_tags) > 0:
            filters = {"tags": "system-ipv" + str(ip_version) + "-works" + "," + extra_tags,
                       "status_name": "Connected", "is_public": True}
        else:
            filters = {"tags": "system-ipv" + str(ip_version) + "-works",
                       "status_name": "Connected", "is_public": True}
    probes = df.byteify(rac.ProbeRequest(**filters))
    print probes
    probesjson = defaultdict(dict)
    print "starting iterator"
    for probe in probes:
        probesjson[probe['id']] = {'ip': probe['address_v'+str(ip_version)],
                'asn': probe['asn_v' + str(ip_version)],
               'country': country_pid[probe['country_code']],
               'id': probe['id']}
        print probesjson[probe['id']]
    print "got probes"
    return probesjson


def get_active_count(mykey=my_key):
    """
    :param mykey: string
    :return: int
    """
    url_path = '/api/v2/measurements/my/?key='+mykey+'&status=1,2'
    request = rac.AtlasRequest(**{"url_path": url_path})
    is_success, results = request.get()
    if is_success:
        return results['count']
    else:
        logger.debug('failed to get active count')
        print results, mykey
        return -1


def get_active_ids(mykey=my_key):
    """
    :param mykey: string
    :return: dict
    """
    url_path = '/api/v2/measurements/my/?key='+mykey+'&status=1,2'
    request = rac.AtlasRequest(**{"url_path": url_path})
    is_success, results = request.get()
    idlist = list()
    if is_success:
        if 'results' in results:
            for res in results['results']:
                idlist.append(res['id'])
    else:
        logger.debug('failed to get active meas IDs')
        print results

    return idlist


def kill_active_meas(mykey=kill_key):
    """
    :param mykey: string
    """
    idlist = get_active_ids()
    for id in idlist:
        atlas_request = rac.AtlasStopRequest(msm_id=id, key=mykey)
        is_success, response = atlas_request.create()
        print is_success
        print response


def ids2string(ids):
    """
    :param ids: list
    :return: str
    """
    vals = ""
    for Id in ids:
        vals += str(Id) + ','
    return vals[:-1]


def make_sources(probe_ids=None, country=None, count=None):
    """
    :param probe_ids: list
    :param country: str
    :param count: int
    :return: rac.AtlasSource
    """
    if type(country) is str and type(count) is int:
        source = rac.AtlasSource(
            type="country",
            value=country,
            requested=count,
            tags={"include": ["system-ipv4-works"]}
        )
    elif type(probe_ids) is list:
        count = len(probe_ids)
        ids = ids2string(probe_ids)
        source = rac.AtlasSource(
            type="probes",
            value=ids,
            requested=count,
            tags={"include": ["system-ipv4-works"]}
        )
    else:
        logger.error('bad params: probe IDs list | country abbrev. & desired probe count')
        raise ValueError("give a list of probe IDs or give a country abbrev. and desired probe count")
    return [source]


def get_probe_info(probe_id):
    """
    :param probe_id: int
    :return: bool, dict
    """
    url_path = "/api/v2/probes/"+str(probe_id)
    request = rac.AtlasRequest(**{"url_path": url_path})
    return request.get()

def make_request(measurement, sources, mykey=my_key):
    """
    :param pings: list
    :param sources: list
    :param mykey: string
    :return: rac.AtlasRequest
    """
    return rac.AtlasCreateRequest(
        start_time=datetime.utcnow(),
        key=mykey,
        measurements=measurement,
        sources=sources,
        is_oneoff=True
    )


def send_request(request):
    """
    :param request: rac.AtlasRequest
    :return: bool, list
    """
    (is_success, response) = request.create()
    if is_success:
        measids = response['measurements']
    else:
        logger.debug('failed to send request: '+str(request)+'; got response: '+str(response))
        print response
        measids = list()
    return is_success, measids


def get_meas_status(measid):
    """
    :param measid: int
    :return: str
    """
    measurement = rac.Measurement(id=measid)
    if measurement.status_id < 3:
        return 'ongoing'
    elif measurement.status_id == 3:
        return 'done'
    else:
        return 'dead'


def get_results(measid, probe_id=None, start=None, stop=None, fmt=None):
    """
    :param measid: int
    :param probe_id: int
    :return: (bool, dict)
    """
    kwargs = {
        "msm_id": measid,
    }

    if probe_id is not None:
        kwargs['probe_ids'] = probe_id
    if start is not None:
        kwargs['start'] = start
    if stop is not None:
        kwargs['stop'] = stop
    if fmt is not None:
        kwargs['format'] = fmt

    is_success, results = rac.AtlasResultsRequest(**kwargs).create()
    if is_success:
        if len(results) > 0:
            if 'result' in results[0].keys():
                return is_success, df.byteify(results[0])
    print results
    logger.debug('failed to get results from '+str(measid))
    return False, results


def get_traceroute(results, pip):
    """
    :param results: dict
    :param pip: str
    :return: list
    """
    traceroute = list()
    try:
        myname = socket.gethostbyaddr(pip)[0]
    except:
        myname = pip
    myasn = asncache.checkcache(pip)
    traceroute.append({'hopnum':0, 'hopip': pip, 'rtt':-1, 'hopname':myname, 'asn':myasn, 'replicas':list()})
    for result in results['result']:
        hop = dict()
        if 'result' in result:
            for packet in result['result']:
                if 'from' in packet:
                    if 'rtt' in packet:
                        hop['rtt'] = packet['rtt']
                    else:
                        hop['rtt'] = -1
                    hop['hopip'] = packet['from']
                    try:
                        hop['hopname'] = socket.gethostbyaddr(hop['hopip'])[0]
                    except:
                        hop['hopname'] = hop['hopip']
                    if 'dst_addr' in results:
                        hop['asn'] = asncache.checkcache(hop['hopip'])
                    hop['replicas'] = list()
                else:
                    hop['hopip'] = '*'

                if 'hop' in result:
                    hop['hopnum'] = result['hop']

                traceroute.append(hop)

    return traceroute


def get_pingdata(results):
    """
    :param results: dict
    :return: dict
    """
    replica = dict()

    if 'dst_addr' in results:
        replica['ip'] = results['dst_addr']
        replica['asn'] = asncache.checkcache(results['dst_addr'])

    if 'avg' in results:
        replica['avgtime'] = results['avg']

    if 'timestamp' in results:
        replica['timeofday'] = results['timestamp']

    return replica
