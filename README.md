# Prometrics

Pluggable server for exporting memtrics to Prometheus.

## Configuration

The following environment variables can be set to configure the system:

  * PROMETRICS_CONFIG - The path to an environment file that sets any of the other
    environment variables.  Settings in the environment will override the settings 
    in the file. Default: /etc/prometrics.conf

  * PROMETRICS_PLUGINPATH - The path to the location of the plugins. Default: plugins
  * PROMETRICS_PORT - The TCP port from which to serve the metrics. Default: 8000

## Plugins Configuration

  * CALLDETAILS_DB - The location of the freeswitch core.db file.  Default: /usr/local/freeswitch/db/core.db