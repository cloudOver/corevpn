all:
	echo Nothing to compile

install:
	mkdir -p $(DESTDIR)/etc/corevpn/
	mkdir -p $(DESTDIR)/etc/corecluster/templates/
	cp -r config/* $(DESTDIR)/etc/corevpn/
	cp -r config/openvpn.template $(DESTDIR)/etc/corecluster/templates/
	mkdir -p $(DESTDIR)/var/lib/cloudOver/coreVpn/certs/
	python3 setup.py install --root=$(DESTDIR)

egg:
	python setup.py sdist bdist_egg

egg_install:
	python setup.py install

egg_upload:
	python setup.py sdist upload

egg_clean:
	rm -rf build/ dist/ corevpn.egg-info/
