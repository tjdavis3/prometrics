
import os
import time
from wsgiref.simple_server import make_server
import logging

from prometheus_client import start_wsgi_server
from pluginbase import PluginBase
from prometheus_client import make_wsgi_app
from prometheus_client.core import CounterMetricFamily 
from prometheus_client import REGISTRY
from envparse import env

log = logging.getLogger(__name__)

class Uptime(object):
    """
    Generates a counter of the total uptime of the process.
    """
    def __init__(self):
        self.start_time = time.time()

    def collect(self):
        """
        Generates a metric of timeticks since startup.
        """
        uptime = time.time() - self.start_time
        yield CounterMetricFamily('prometrics_uptime_seconds', 
            'The number of seconds since startup.', uptime
            )


def load_plugins(search_path=None):
    """
    Loads the plugin source based on the list of paths passed in.

    :Params:
       search_path list:  List of directories containing prometheus plugins.

    :Returns:
        A pluginbase plugin_source that can be used to import plugins.
    """

    plugin_base = PluginBase('plugins')
    if search_path is None:
        pluginpath = os.path.dirname(os.path.abspath(__file__))
        pluginpath = os.path.join(pluginpath, 'plugins')
        search_path = [pluginpath]
    log.debug('Creating plugin source for %s' % str(search_path))
    plugin_source = plugin_base.make_plugin_source(
        searchpath=search_path)
    return plugin_source
    
if __name__ == '__main__':
    logging.root.setLevel(logging.DEBUG)
    env.read_envfile(env('PROMETRICS_CONFIG', default='/etc/prometrics.conf'))
    plugins = load_plugins(env('PROMETRICS_PLUGINPATH', default=None))
    REGISTRY.register(Uptime())
    for plugin in plugins.list_plugins():
        log.info('Loading plugin %s...' % plugin)
        plugins.load_plugin(plugin)
    app = make_wsgi_app()
    httpd = make_server('', env('PROMETRICS_PORT', default=8000, cast=int), app)
    httpd.serve_forever()

    