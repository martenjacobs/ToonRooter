#!/bin/sh
set -e

#create urandom which is missing on a 5.0.4 toon in u-booted shell
if [ ! -e /dev/urandom ] ; then
  mknod /dev/urandom c 1 9
fi

if [ $# -eq 0 ]; then
  PASS=`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | head -c 10`
else
  PASS="$1"
fi

cd `dirname "$0"`

PASSENC=`/usr/bin/openssl passwd -crypt $PASS 2>/dev/null`

echo ">>> Enabling root user. Your root password is: $PASS"
if [[ ! -f /etc/passwd.preroot ]]; then
  cp /etc/passwd /etc/passwd.preroot
fi
sed -i -e "s#root:[^:]*#root:$PASSENC#" /etc/passwd

echo ">>> Opening ports 22, 80 and 10080 on firewall"
if [[ ! -f /etc/default/iptables.conf.preroot ]]; then
  cp /etc/default/iptables.conf /etc/default/iptables.conf.preroot
fi
sed -i -e "s/^# These are all closed for Quby\/Toon:/# ADDED WHILE ROOTING\n\
-A HCB-INPUT -p tcp -m tcp --dport 22 --tcp-flags SYN,RST,ACK SYN -j ACCEPT\n\
-A HCB-INPUT -p tcp -m tcp --dport 10080 --tcp-flags SYN,RST,ACK SYN -j ACCEPT\n\
-A HCB-INPUT -p tcp -m tcp --dport 80 --tcp-flags SYN,RST,ACK SYN -j ACCEPT\n\
# END/" /etc/default/iptables.conf

echo ">>> Disable VPN on boot"
sed -i 's~ovpn:235~#ovpn:235~g' /etc/inittab

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
# append our key to the authorized keys file
cat id_rsa.pub >> /root/.ssh/authorized_keys
# append a line feed
echo >> /root/.ssh/authorized_keys

# TODO: remove duplicate lines from authorized_keys. This may do the trick:
# awk '!a[$0]++' /root/.ssh/authorized_keys
