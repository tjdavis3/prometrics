import sqlite3
import logging

from prometheus_client.core import GaugeMetricFamily 
from prometheus_client import REGISTRY
from envparse import env

log = logging.getLogger(__name__)
SQL = 'select context,callstate,count(*) from channels group by context,callstate union select context,"CALLS",count(*) from detailed_calls group by context;'

class CallDetails(object):
    """
    Gathers call details from the freeswitch core.db database.

    Configuration:
      CALLDETAILS_DB - Enviornment variable that indicates the full path to core.db.
    """
    def collect(self):
        conn = None
        curs = None
        try:
            conn = sqlite3.connect(env('CALLDETAILS_DB', default='/usr/local/freeswitch/db/core.db'))
            curs = conn.cursor()
            gauge = GaugeMetricFamily('freeswitch_calldetail',
                'Current call volumes',
                labels=['carrier', 'disposition'])
            for row in curs.execute(SQL):
                gauge.add_metric([row[0], row[1]], float(row[2]))
            yield gauge
        except Exception, e:
            log.error(str(e))
        finally:
            if curs:
                try:
                    curs.close()
                except:
                    pass
            if conn:
                try:
                    conn.close()
                except:
                    pass
REGISTRY.register(CallDetails())