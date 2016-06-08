Name: corevpn
Version: 16.06.01
Release: 1%{?dist}
URL: http://www.cloudover.org/corecluster/
Packager: Maciej Nabozny <maciej.nabozny@cloudover.io>
Summary: OpenVPN support for CoreCluster
License: GPLv3

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

Requires: corecluster
Requires: openvpn
Requires: openssl

%description
VPN extension for CoreCluster

%install
rm -rf $RPM_BUILD_ROOT
cd corevpn/
make install DESTDIR=$RPM_BUILD_ROOT

%post
echo "coreVpn: Changing permissions"
chmod -R 700 /var/lib/cloudOver/coreVpn/certs/
chown -R cloudover:cloudover /var/lib/cloudOver/coreVpn/certs

if ! [ -f /etc/corevpn/config.py ] ; then
    echo "coreVpn: Creating default config file"
    cp /etc/corevpn/config.example /etc/corevpn/config.py
fi

echo "coreVpn: Adding sudo commands for cloudover user"
echo "cloudover ALL=NOPASSWD: /usr/sbin/openvpn" > /etc/sudoers.d/corevpn
echo "cloudover ALL=NOPASSWD: /usr/sbin/brctl" >> /etc/sudoers.d/corevpn

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
/etc/corevpn/
/etc/corecluster/templates/
/usr/local/lib/python2.7/dist-packages/
