import base64
import dns.message
from warriorpy.net_tools import ipparsing as ipp
##################################################################
#                           LOGGING
##################################################################
import logging
import logging.config

logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

# create logger
logger = logging.getLogger(__name__)
logger.debug(__name__+"logger loaded")

##################################################################
#                             CODE
##################################################################


def decode_dns(datastr):
    """
    :param datastr: str
    :return: dns.message
    """
    return dns.message.from_wire(base64.b64decode(datastr))


def isbadquery(data):
    for res in data['resultset']:
        if 'error' in res:
            return True
    return False


def parse_dns_json(data):
    """
    :param data: dict
    :return: dict
    """
    ret = dict()
    try:
        ret['probe_ip'] = ipp.ip2int(data['from'])
    except:
        ret['probe_ip'] = data['from']
        logger.error("failed to convert: "+data['from'])
    ret['probe_id'] = data['prb_id']
    ret['time'] = data['timestamp']
    ret['ipv4'] = dict()
    ret['ipv6'] = dict()
    for res in data['resultset']:
        if res['af'] == 4:
            ipv = 'ipv4'
            ret[ipv]['perceived_ldns'] = ipp.ip2int(res['dst_addr'])
            ret[ipv]['perceived_ip'] = ipp.ip2int(res['src_addr'])
            try:
                dnsmsg = decode_dns(res['result']['abuf'])
                if len(dnsmsg.answer) > 0:
                    ret['domain'] = dnsmsg.answer[0].name.to_text().lower()
                    ret[ipv]['ttl'] = dnsmsg.answer[0].ttl
                    ret[ipv]['answer_ip_list'] = list()
                    for i in dnsmsg.answer[0].items:
                        ret[ipv]['answer_ip_list'].append(ipp.ip2int(i.to_text()))
            except Exception as e:
                logger.error('exception: '+str(e))
        else:
            ipv = 'ipv6'
            ret[ipv]['perceived_ldns'] = res['dst_addr']
            ret[ipv]['perceived_ip'] = res['src_addr']
            try:
                dnsmsg = decode_dns(res['result']['abuf'])
                if len(dnsmsg.answer) > 0:
                    ret['domain'] = dnsmsg.answer[0].name.to_text().lower()
                    ret[ipv]['ttl'] = dnsmsg.answer[0].ttl
                    ret[ipv]['answer_ip_list'] = list()
                    for i in dnsmsg.answer[0].items:
                        ret[ipv]['answer_ip_list'].append(i.to_text())
            except Exception as e:
                logger.error('exception: '+str(e))
        #what ldns did the probe think it was using?
        if ipp.is_local(res['dst_addr']):
            ret['private_ldns_'+ipv] = True
        else:
            ret['private_ldns_'+ipv] = False
        if ipp.is_local(res['src_addr']):
            ret['private_self_'+ipv] = True
        else:
            ret['private_self_'+ipv] = False
        ret[ipv]['raw_result'] = res['result']['abuf']
        ret[ipv]['rtt_sec'] = res['result']['rt']
        ret[ipv]['ANCOUNT'] = res['result']['ANCOUNT']
        ret[ipv]['ARCOUNT'] = res['result']['ARCOUNT']
        ret[ipv]['NSCOUNT'] = res['result']['NSCOUNT']
        ret[ipv]['QDCOUNT'] = res['result']['QDCOUNT']
        ret[ipv]['query_id'] = res['result']['ID']
        ret[ipv]['size'] = res['result']['size']
    return ret
