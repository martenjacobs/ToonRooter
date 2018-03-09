#!/bin/sh
set -e

cd `dirname "$0"`

echo ">>> Enabling root user"
if [[ ! -f /etc/passwd.preroot ]]; then
  cp /etc/passwd /etc/passwd.preroot
fi
sed -i -e 's/^root:DISABLED:/root::/' /etc/passwd

echo ">>> Opening ports 22, 80 and 10080 on firewall"
if [[ ! -f /etc/default/iptables.conf.preroot ]]; then
  cp /etc/default/iptables.conf /etc/default/iptables.conf.preroot
fi
sed -i -e "s/^# These are all closed for Quby\/Toon:/# ADDED WHILE ROOTING\n\
-A HCB-INPUT -p tcp -m tcp --dport 22 --tcp-flags SYN,RST,ACK SYN -j ACCEPT\n\
-A HCB-INPUT -p tcp -m tcp --dport 10080 --tcp-flags SYN,RST,ACK SYN -j ACCEPT\n\
-A HCB-INPUT -p tcp -m tcp --dport 80 --tcp-flags SYN,RST,ACK SYN -j ACCEPT\n\
# END/" /etc/default/iptables.conf

set +e

echo ">>> Installing dropbear"
opkg install dropbear_2015.71-r0_qb2.ipk
if [[ $? == 255 ]] ; then
  set -e
  sh /usr/lib/opkg/info/dropbear.postinst
fi

set +e
echo ">>> Installing openssh-sftp-server"
opkg install openssh-sftp-server_7.3p1-r10.0_qb2.ipk
if [[ $? == 255 ]] ; then
  set -e
  sh /usr/lib/opkg/info/dropbear.postinst
fi

set -e

mkdir -p /root/.ssh/
cat <<EOF > /root/.ssh/authorized_keys
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC2EwjrFPhqFidiQswrSG/2srO9iiZM6R08PvLxT9xKGsAOGIEIbGVb19BmtfHVQYWpMktpfJt8cFDX9YIrPvluE2l735yrKz5tYe4+t5yb7WKmYVVMO1RNK8Iwl3ck0baAskLLLa9oX+AnDIqTZQUZhbp6N2lCdCanFYoZNztoGOBHAdbYNaewp6Oy6/m/yegcw6y8bS0SWs89tV8/ZfxIjIJI+prlnEUrtr/gsOZXXWrAixIiGU+Pqb8M9InWJbKTP1iHNUf+cEHYulEtZbK0Csk9XUHFOiDmjqzBT16BaaK9CAC/Ddh/vOqZ+Mz1SnheGcSvO8Na4VJfgIhropjz
EOF
