DESTDIR=/

all:
	echo "Nothing to compile"

install:
	mkdir -p $(DESTDIR)/usr/lib/cloudOver/
	cp -r lib/overCluster $(DESTDIR)/usr/lib/cloudOver/

	mkdir -p $(DESTDIR)/etc/cloudOver/
	cp -r etc/overClusterConf $(DESTDIR)/etc/cloudOver/
	cp -r etc/coreVpnConf $(DESTDIR)/etc/cloudOver/
	cp $(DESTDIR)/etc/cloudOver/coreVpnConf/config.example $(DESTDIR)/etc/cloudOver/coreVpnConf/config.py

	mkdir -p $(DESTDIR)/var/lib/cloudOver/coreVpn/certs/
	mkdir -p $(DESTDIR)/var/log/cloudOver/coreVpn/
	mkdir -p $(DESTDIR)/var/run/

	mkdir -p $(DESTDIR)/etc/sudoers.d/
	echo "cloudover ALL=NOPASSWD: /usr/sbin/openvpn" >> $(DESTDIR)/etc/sudoers.d/corevpn
	echo "cloudover ALL=NOPASSWD: /bin/kill" >> $(DESTDIR)/etc/sudoers.d/corevpn

