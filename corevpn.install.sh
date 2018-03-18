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
