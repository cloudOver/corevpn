DESTDIR=/

all:
	echo "Nothing to compile"

install:
	mkdir -p $(DESTDIR)/usr/lib/cloudOver/
	cp -r lib/overCluster $(DESTDIR)/usr/lib/cloudOver/

	mkdir -p $(DESTDIR)/var/lib/cloudOver/coreVpn/certs/
	mkdir -p $(DESTDIR)/var/log/cloudOver/coreVpn/
	mkdir -p $(DESTDIR)/var/run/

	mkdir -p $(DESTDIR)/etc/sudoers.d/
	echo "cloudover ALL=NOPASSWD: /usr/sbin/openvpn" >> $(DESTDIR)/etc/sudoers.d/corevpn
	echo "cloudover ALL=NOPASSWD: /bin/kill" >> $(DESTDIR)/etc/sudoers.d/corevpn

