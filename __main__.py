
import argparse, os, re


supported_jtag_hardware=['auto']
try:
    for file in os.listdir("assets/adapters"):
        m=re.match(r"^(.+)\.cfg$", file)
        if m:
            supported_jtag_hardware.append(m.group(1))
except:
    pass


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

parser.add_argument('--jtag-available',         action='store_true', help='Indicates you have a JTAG debugger connected to your Toon\'s JTAG headers')
parser.add_argument('--jtag-hardware',
                        metavar='TYPE',
                        help='The JTAG debugger type that we\'re working with. The default is to autodetect the JTAG debugger (which currently only works on Raspberry Pi). Supported values are: {}'.format(', '.join(supported_jtag_hardware)),
                        default="auto")

parser.add_argument('--dont-check-uboot',       action='store_true', help='Don\'t check whether we can access the installer version of U-Boot before using JTAG to start up the custom one.')
parser.add_argument('--dont-cleanup-payload',   action='store_true', help='Leave the payload in /payload. Use this if you want to include more files and do something with them.')
parser.add_argument('--dont-reboot-after',      action='store_true', help='Don\'t reboot the Toon after rooting it. Use this if you want to use the serial console after rooting')
parser.add_argument('--uboot-only',             action='store_true', help='Only boot to the u-boot environment for manual control.')
parser.add_argument('--boot-only',              action='store_true', help='Don\'t install the payload, just boot into the serial console')


args = parser.parse_args()

import logging
logging.basicConfig(level={
    "INFO":logging.INFO,
    "DEBUG":logging.DEBUG,
}[args.output_level])
log = logging.getLogger(__name__)

def get_cpuinfo():
    info = {}
    with open('/proc/cpuinfo') as fo:
        for line in fo:
            name_value = [s.strip() for s in line.split(':', 1)]
            if len(name_value) != 2:
                continue
            name, value = name_value
            if name not in info:
                info[name]=[]
            info[name].append(value)
    return info
def find_rpi_version():
    try:
        revision = get_cpuinfo()['Revision'][0]
        # Source: https://www.raspberrypi.org/documentation/hardware/raspberrypi/revision-codes/README.md
        return {
            "Beta": "rpi1",
            "0002": "rpi1",
            "0003": "rpi1",
            "0004": "rpi1",
            "0005": "rpi1",
            "0006": "rpi1",
            "0007": "rpi1",
            "0008": "rpi1",
            "0009": "rpi1",
            "000d": "rpi1",
            "000e": "rpi1",
            "000f": "rpi1",
            "0010": "rpi1",
            "0011": "rpi1",
            "0012": "rpi1",
            "0013": "rpi1",
            "0014": "rpi1",
            "0015": "rpi1",
            "900021": "rpi1",
            "900032": "rpi1",
            "900092": "rpi1",
            "900093": "rpi1",
            "9000c1": "rpi1",
            "9020e0": "rpi3",
            "920092": "rpi1",
            "920093": "rpi1",
            "900061": "rpi1",
            "a01040": "rpi2",
            "a01041": "rpi2",
            "a02082": "rpi3",
            "a020a0": "rpi3",
            "a020d3": "rpi3",
            "a02042": "rpi2",
            "a21041": "rpi2",
            "a22042": "rpi2",
            "a22082": "rpi3",
            "a220a0": "rpi3",
            "a32082": "rpi3",
            "a52082": "rpi3",
            "a22083": "rpi3",
            "a02100": "rpi3",
            "a03111": "rpi4",
            "b03111": "rpi4",
            "c03111": "rpi4",
        }[revision]
    except:
        pass
    return None

def detect_jtag_hardware():
    hardware=find_rpi_version()# or detect_usb_device() or detect_something_else()
    #TODO: implement more checks here
    if not hardware:
        raise Exception("Cannot autodetect jtag hardware")
    return hardware

def main():

    log.info("Starting up...")

    import rooter

    serial_path = args.serial_port
    jtag_available = args.jtag_available
    jtag_hardware = args.jtag_hardware
    check_current_bootloader = not args.dont_check_uboot
    cleanup_payload = not args.dont_cleanup_payload
    reboot_after = not args.dont_reboot_after
    uboot_only = args.uboot_only
    boot_only = args.boot_only

    if jtag_hardware == "auto":
        jtag_hardware = detect_jtag_hardware()
        log.info("Detected JTAG hardware '{}'".format(jtag_hardware))

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
    params = {
        "port" : serial_path,
        "ssh_pubkey_data" : ssh_pubkey_data,
        "has_jtag" : jtag_available,
        "check_uboot" : check_current_bootloader,
        "cleanup_payload" : cleanup_payload,
        "reboot_after" : reboot_after,
        "uboot_only" : uboot_only,
        "boot_only" : boot_only,
        "jtag_hardware" : jtag_hardware
    }
    log.debug(json.dumps(params))
    rooter.Rooter(**params).run()

if __name__ == '__main__' :
    try:
        main()
    except Exception as e:
        if args.output_level=="DEBUG":
            raise
        else:
            log.fatal(str(e))
