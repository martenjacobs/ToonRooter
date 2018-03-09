
import argparse


parser = argparse.ArgumentParser(prog='sudo python .',
                                 description='Root your Toon.')

parser.add_argument('--serial-port',
                        metavar='PATH',
                        help='The path of the serial port to use',
                        default='/dev/serial0')

parser.add_argument('--ssh-public-key',
                        metavar='PATH',
                        help='The path to an RSA public key which should be an allowed key on the Toon after rooting it. If not supplied, a key pair is generated',
                        default=None)
parser.add_argument('--output-ssh-key',
                        metavar='PATH',
                        help='The path to output a generated key pair (the public key will have a .pub suffix). Default is to write id_rsa and id_rsa.pub in the current directory. Ignored if you\'ve used --ssh-public-key',
                        default="./id_rsa")
parser.add_argument('--private-key-password',
                        metavar='PASSWORD',
                        help='The password that should be used to encrypt the private key when it\'s generated. Default is to use no encryption. Ignored if you\'ve used --ssh-public-key',
                        default=None)
parser.add_argument('--output-level',
                        metavar='INFO|DEBUG',
                        help='The level of output to print to the console',
                        default="INFO")

parser.add_argument('--jtag-available',         action='store_true', help='Indicates you have your Pi connected to your Toon\'s JTAG headers')
parser.add_argument('--dont-check-uboot',       action='store_true', help='Don\'t check whether we can access the installer version of U-Boot before using JTAG to start up the custom one.')
parser.add_argument('--dont-cleanup_payload',   action='store_true', help='Leave the payload in /payload. Use this if you want to include more files and do something with them.')
parser.add_argument('--dont-reboot_after',      action='store_true', help='Don\'t reboot the Toon after rooting it. Use this if you want to use the serial console after rooting')
parser.add_argument('--boot-only',              action='store_true', help='Don\'t install the payload, just boot into the serial console')


args = parser.parse_args()

import logging
logging.basicConfig(level={
    "INFO":logging.INFO,
    "DEBUG":logging.DEBUG,
}[args.output_level])
log = logging.getLogger(__name__)

log.info("Starting up...")

import rooter

serial_path = "/dev/serial0"
jtag_available = args.jtag_available
check_current_bootloader = not args.dont_check_uboot
cleanup_payload = not args.dont_cleanup_payload
reboot_after = not args.dont_reboot_after
boot_only = args.boot_only

import sshkeys
if args.ssh_public_key:
    with open(args.ssh_public_key, 'r') as f:
        ssh_pubkey_data = f.read()
    if not sshkeys.check_public_key(ssh_pubkey_data):
        raise Exception("RSA key is not valid")
    log.info("Using RSA key in {}".format(args.ssh_public_key))
else:
    (pub, priv) = sshkeys.generate_key_pair(args.private_key_password)
    ssh_pubkey_data = pub
    with open("{}".format(args.output_ssh_key), 'w') as f:
        f.write(priv)
    with open("{}.pub".format(args.output_ssh_key), 'w') as f:
        f.write(pub)
    log.info("Written private and public key pair to {0} and {0}.pub, respectively".format(args.output_ssh_key))

import json
log.debug(json.dumps({
    "path" : serial_path,
    "ssh_pubkey_data" : ssh_pubkey_data,
    "has_jtag" : jtag_available,
    "check_uboot" : check_current_bootloader,
    "cleanup_payload" : cleanup_payload,
    "reboot_after" : reboot_after,
    "boot_only" : boot_only
}))
r"""
rooter.root(
    path = serial_path,
    ssh_pubkey_data = ssh_pubkey_data,
    has_jtag = jtag_available,
    check_uboot = check_current_bootloader,
    cleanup_payload = cleanup_payload,
    reboot_after = reboot_after,
    boot_only = boot_only)"""
