# WebHCat Management Pack

Management pack for adding WebHCat to Hive 3.0

Installation:

- check out the project webhcat_mp
- mvn clean package
- copy target/webhcat-mpack-1.0.0.tar.gz to the ambari-server host
- ambari-server stop
- ambari-server install-mpack --mpack=/path/to/webhcat-mpack-1.0.0.tar.gz
- ambari-server start

After logging into ambari again WebHCat will be present in the list of services. I'll require Hive to be installed as well, and will work with the Hive installed at the same cluster.

