DESTDIR=/

all:
	echo "Nothing to compile"

install:
	mkdir -p $(DESTDIR)/usr/lib/cloudOver/
	cp -r lib/overCluster $(DESTDIR)/usr/lib/cloudOver/

	mkdir -p $(DESTDIR)/var/lib/cloudOver/coreVpn/certs/
	mkdir -p $(DESTDIR)/var/log/cloudOver/coreVpn/
	mkdir -p $(DESTDIR)/var/run/
	chmod 600 $(DESTDIR)/var/lib/cloudOver/coreVpn/certs/
	chown cloudover:cloudover $(DESTDIR)/var/lib/cloudOver/coreVpn/secrets
