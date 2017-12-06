"""
This plugin pulls SNMP information from the bladecenter.

"""

import netsnmp
import re
import threading
import atexit
from time import sleep
from prometheus_client import REGISTRY
from prometheus_client.core import GaugeMetricFamily as Gauge

number_re = re.compile('(\d+\.?\d+)\D*')
_POWER_USED = '.1.3.6.1.4.1.2.3.51.2.2.10.1.1.1.10'
_TEMP = '.1.3.6.1.4.1.2.3.51.2.2.1.5.1.0'
_SLEEP_TIME = 30
_POWER_USED_METRIC = 'bladecenter_power_used_watts'
_TEMP_METRIC = 'bladecenter_ambient_temp'
POOL_TIME=25
dataLock = threading.Lock()
metrics = {}

BC_HOSTS = [
    'bc01.den.teliax.com',
    'bc02.den.teliax.com',
    'bc03.den.teliax.com',
    'bc04.den.teliax.com',
    'bc05.den.teliax.com',
    'bc06.den.teliax.com',
    'bc07.den.teliax.com',
    'bc08.den.teliax.com',
    'bc09.den.teliax.com',
    'bc10.den.teliax.com',
    'bc11.den.teliax.com',
    'bc12.den.teliax.com',
]

snmpThread = threading.Thread()

def create_collector():
    collector = BladeCenterCollector()

    def interrupt():
        global snmpThread
        snmpThread.cancel()

    def collect():
        global metrics
        global snmpThread
        with dataLock:
        # Do your stuff with jobList Here
            for host in BC_HOSTS:
                if not host in metrics:
                    metrics[host] = {}
                metrics[host]['power'] = get_power_used(host)
                metrics[host]['temp'] = get_temp(host)

        # Set the next thread to happen
        snmpThread = threading.Timer(POOL_TIME, collect, ())
        snmpThread.start()

    def doCollectStart():
        # Do initialisation stuff here
        global snmpThread
        # Create your thread
        snmpThread = threading.Timer(POOL_TIME, collect, ())
        snmpThread.start()

    # Initiate
    doCollectStart()
    # When you kill Flask (SIGTERM), clear the trigger for the next thread
    atexit.register(interrupt)
    return collector

def _parse_number(snmp_result):
    if snmp_result is None:
        return 0
    mat = number_re.match(snmp_result)
    if mat:
        amps =  mat.groups()[0]
        return float(amps)
    else:
        return 0

def get_power_used(host):
    """
    Pulls the power used and returns a tuple of ints in watts.
    """
    var = netsnmp.Varbind(_POWER_USED)
    result = netsnmp.snmpwalk(var, Version=1, DestHost=host, Community='public')
    if len(result) == 2:
        pd1 = result[0]
        pd2 = result[1]
    else:
        pd1 = pd2 = '-1'
    return (_parse_number(pd1), _parse_number(pd2))


def _c_to_f(temp):
    return float(temp * 9 / 5 + 32)

def get_temp(host):
    var = netsnmp.Varbind(_TEMP)
    snmptemp = netsnmp.snmpget(var, Version=1, DestHost=host, Community='public')
    temp = float(_parse_number(snmptemp[0]))
    temp = _c_to_f(temp)
    return temp

class BladeCenterCollector(object):

    def __init__(self):
        super(BladeCenterCollector, self).__init__()

    def collect(self):
        pwr = Gauge(_POWER_USED_METRIC, 'Amount of power being consumed in watts',
                  labels=['instance', 'power_domain'])
        temp = Gauge(_TEMP_METRIC, 'Ambient Temperature',
                  labels=['instance', ])

        for host, host_metrics in metrics.items():
            power_metrics =  host_metrics.get('power')
            if power_metrics is not None:
                pwr.add_metric([host, '1'], power_metrics[0])
                pwr.add_metric([host, '2'], power_metrics[1])
            temp.add_metric([host], host_metrics.get('temp', -1))

        yield pwr
        yield temp

bladecenter_collector = create_collector()
if not __name__ == '__main__':
    REGISTRY.register(bladecenter_collector)
else:
    import sys
    host = sys.argv[1] + '.den.teliax.com'
    bc = create_collector()
    print "Power ", host, ':', bc.get_power_used(host)
    print "Temp ", host, ':', bc.get_temp(host)
