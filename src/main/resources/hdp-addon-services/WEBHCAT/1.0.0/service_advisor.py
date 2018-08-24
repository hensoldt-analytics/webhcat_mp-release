#!/usr/bin/env ambari-python-wrap

import imp
import os
import socket
import traceback

from resource_management.core.logger import Logger

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
STACKS_DIR = os.path.join(SCRIPT_DIR, 'stacks')
PARENT_FILE = os.path.join(STACKS_DIR, 'service_advisor.py')

try:
  with open(PARENT_FILE, 'rb') as fp:
    service_advisor = imp.load_module('service_advisor', fp, PARENT_FILE, ('.py', 'rb', imp.PY_SOURCE))
except Exception as e:
  traceback.print_exc()
  print "Failed to load parent"

class HDP26DATAANALYTICSSTUDIOServiceAdvisor(service_advisor.ServiceAdvisor):

  def __init__(self, *args, **kwargs):
    self.as_super = super(HDP26DATAANALYTICSSTUDIOServiceAdvisor, self)
    self.as_super.__init__(*args, **kwargs)

  def getHostForComponent(self, component, hostsList):
    if len(hostsList) == 0:
      return None

    componentName = self.getComponentName(component)
    if componentName == "DATA_ANALYTICS_STUDIO_POSTGRESQL_SERVER":
      # The local host with ambari is likely to have postgresql installed on it, do not put Data Analytics Studios DB here
      result = os.system("which psql > /dev/null 2>&1")
      if result == 0:
        Logger.info("Ambari host ({0}) has postgresql db, looking for other host for DATA_ANALYTICS_STUDIO_POSTGRESQL_SERVER"
                    .format(socket.getfqdn()))
        for host in hostsList:
          if host != socket.getfqdn():
            Logger.info("DATA_ANALYTICS_STUDIO_POSTGRESQL_SERVER was put into " + host)
            return host
    
    return super(HDP26DATAANALYTICSSTUDIOServiceAdvisor, self).getHostForComponent(component, hostsList)

  def colocateService(self, hostsComponentsMap, serviceComponents):
    for hostName in hostsComponentsMap.keys():
      hostComponents = hostsComponentsMap[hostName]
      
      isDasClient = {"name": "DATA_ANALYTICS_STUDIO_CLIENT"} in hostComponents
      isHS2 = {"name": "HIVE_SERVER"} in hostComponents
      isHSI = {"name": "HIVE_SERVER_INTERACTIVE"} in hostComponents
      isHiveClient = {"name": "HIVE_CLIENT"} in hostComponents
      isHive = isHS2 or isHSI or isHiveClient
      
      if not isDasClient and isHive:
        hostComponents.append({"name": "DATA_ANALYTICS_STUDIO_CLIENT"})
      if isDasClient and not isHive:
        hostComponents.remove({"name": "DATA_ANALYTICS_STUDIO_CLIENT"})
  
  def getServiceComponentLayoutValidations(self, services, hosts):
    items = []
    
    componentsListList = [service["components"] for service in services["services"]]
    componentsList = [item["StackServiceComponents"] for sublist in componentsListList for item in sublist]
    dasPostgresqlServerHost = self.getHosts(componentsList, "DATA_ANALYTICS_STUDIO_POSTGRESQL_SERVER")[0]
    
    result = os.system("which psql > /dev/null 2>&1")
    if result == 0 and socket.getfqdn() == dasPostgresqlServerHost:
      items.append( { "type": 'host-component',
                      "level": 'WARN',
                      "message": "Data Analytics Studio PostgreSQL Server is put on the same host as Ambari, where it is running it's own PostgreSQL server. The two may collide.",
                      "component-name": 'DATA_ANALYTICS_STUDIO_POSTGRESQL_SERVER',
                      "host": dasPostgresqlServerHost } )
    
    return items

  def getServiceConfigurationRecommendations(self, configurations, clusterSummary, services, hosts):
    putTezSiteProperty = self.putProperty(configurations, "tez-site", services)
    
    putTezSiteProperty("tez.aux.uris", "${fs.defaultFS}/apps/tez/aux-libs/")
    putTezSiteProperty("tez.history.logging.service.class", "com.hortonworks.hivestudio.eventshook.tezhook.HdfsHistoryLoggingService")
    

