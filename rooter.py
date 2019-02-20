import serial
import logging
import re
import telnetlib
import os
import subprocess
import tarfile
import base64
import string
import random
from time import sleep
from serial.serialutil import Timeout
import StringIO
import tempfile

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

class Rooter(object):
    def __init__(self, **params):
        if type(params['port']) is str:
            params['port']=serial.Serial(
                port=params['port'],
                baudrate=115200
            )
        self._port = params['port']
        self._ssh_pubkey_data = params['ssh_pubkey_data']
        self._has_jtag = params['has_jtag']
        self._check_uboot = params['check_uboot']
        self._cleanup_payload = params['cleanup_payload']
        self._reboot_after = params['reboot_after']
        self._uboot_only = params['uboot_only']
        self._boot_only = params['boot_only']
        self._jtag_hardware = params['jtag_hardware']

    def run(self):
        #TODO: clean this up
        port = self._port
        ssh_pubkey_data = self._ssh_pubkey_data
        has_jtag = self._has_jtag
        check_uboot = self._check_uboot
        cleanup_payload = self._cleanup_payload
        reboot_after = self._reboot_after
        uboot_only = self._uboot_only
        boot_only = self._boot_only

        if check_uboot:
            uboot_passwords={
                "2010.09-R6" : "f4E9J",
                "2010.09-R8" : "3BHf2",
                "2010.09"    : "toon"
            }
            log.info("Waiting for Toon to restart")
            uboot_version=self.read_uboot_version()
            log.info("Toon has U-Boot version {}".format(uboot_version))
            if uboot_version in uboot_passwords:
                log.info("Using password to log in")
                self.access_uboot(uboot_passwords[uboot_version])
                if uboot_only:
                    log.info("Your Toon is now waiting in u-boot. You can you use a serial console for manual control.")
                else:
                    self.patch_uboot()
                    if boot_only:
                        log.info("Your Toon is now booting into a serial console")
                    else:
                        log.info("Waiting for boot up")
                        self.write_payload()
                        self.patch_toon()
                        log.info("Your Toon is now rooted. Please wait for it to boot up and try to log in using SSH")
                return
            elif has_jtag is False:
                log.error("Unable to log in using password (need JTAG, but it's disabled)")
                return
        if has_jtag:
            log.info("Loading new bootloader")
            self.start_bootloader("assets/u-boot.bin")
            port.reset_input_buffer()
            self._has_jtag = False
            self._check_uboot = True
            self.run()
        else:
            log.error("Need JTAG when rooting without manual reset")
            return

    def read_uboot_version(self):
        version_line_match = re.compile(r'^U-Boot ([^ ]+)')
        while True:
            line = self._port.readline().strip()
            match = version_line_match.match(line)
            if match:
                return match.group(1)

    def access_uboot(self, password):
        log.info("Logging in to U-Boot")
        self._port.write(password)
        self._port.flush()
        log.debug(self._port.read_until("U-Boot>"))
        log.debug("Logged in to U-Boot")

    def patch_uboot(self):
        port = self._port

        log.info("Patching U-Boot")
        port.reset_input_buffer()
        sleep(0.1)
        port.write("printenv\n")
        port.flush()
        add_misc_match = re.compile(r'^addmisc=(.+)$')
        add_misc_val = None

        sleep(0.5)

        lines = port.read_until("U-Boot>")
        log.debug(lines)
        for line in lines.split('\n'):
            line = line.strip()
            log.debug(line)
            match = add_misc_match.match(line)
            if match:
                add_misc_val = match.group(1)

        if add_misc_val is None:
            log.error("Could not find value for addmisc environment variable")
            return

        cmd = "setenv addmisc " + re.sub(r'([\$;])',r'\\\1', add_misc_val + " init=/bin/sh")
        port.write(cmd + "\n")
        port.flush()
        log.debug(port.read_until("U-Boot>"))
        port.write("run boot_nand\n")
        port.flush()

    def create_payload_tar(self):
        tar_path = tempfile.mkstemp(suffix=".tar.gz")[1]
        ssh_key = self._ssh_pubkey_data
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add('payload/', arcname='payload')

            ssh_key_str = StringIO.StringIO(ssh_key)

            info = tarfile.TarInfo(name="payload/id_rsa.pub")
            info.size=len(ssh_key)

            tar.addfile(tarinfo=info, fileobj=StringIO.StringIO(ssh_key))
        return tar_path

    def write_payload(self):
        port = self._port
        tar_path = self.create_payload_tar()

        log.debug(port.read_until("/ # "))
        port.write("base64 -d | tar zxf -\n")
        port.flush()
        #(tarr, tarw) = os.pipe()
        #tar = tarfile.open(mode='w|gz', fileobj=tarw)
        #tar.add("payload/patch_toon.sh")

        log.info("Transferring payload")
        with open(tar_path, 'r') as f:
            base64.encode(f, port)

        os.remove(tar_path)

        port.flush()
        port.reset_input_buffer()
        port.write("\x04")
        port.flush()

    def patch_toon(self):
        (port, clean_up, reboot) = (
            self._port, self._cleanup_payload, self._reboot_after)
        log.info("Patching Toon")
        log.debug(port.read_until("/ # "))
        password = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        port.write("sh payload/patch_toon.sh \"{}\"\n".format(password))
        try:
            while True:
                line = read_until(port, ["/ # ", "\n"])
                if line == "/ # ":
                    break
                if line.startswith(">>>"):
                    log.info(line.strip())
                else:
                    log.debug(line.strip())
        except:
            log.exception("Script failed")
            sleep(5)
        if clean_up:
            log.info("Cleaning up")
            port.write("rm -r payload\n")
            log.debug(port.read_until("/ # "))
        if reboot:
            log.info("Rebooting")
            port.write("/etc/init.d/reboot\n")

    def start_bootloader(self, bin_path):

        log.info("Starting openocd")

        proc = subprocess.Popen([
            'openocd',
                '-s', '/usr/share/openocd',
                '-f', 'assets/adapters/{}.cfg'.format(self._jtag_hardware),
                '-f', 'assets/boards/ed20.cfg'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        try:
            wait = 10
            log.info("Waiting for {} seconds".format(wait))
            sleep(wait)
            client = telnetlib.Telnet('localhost', 4444)
            log.debug(client.read_until("> "))
            log.info("Halting CPU")
            client.write("soft_reset_halt\n")
            log.debug(client.read_until("> "))
            sleep(0.1)
            client.write("reset halt\n")
            log.debug(client.read_until("> "))
            sleep(0.1)
            log.info("Loading new image to RAM")
            client.write("load_image {} 0xa1f00000\n".format(bin_path))
            log.debug(client.read_until("> "))
            sleep(0.1)
            log.info("Starting up new image")
            client.write("resume 0xa1f00000\n")
        except:
            try:
                log.exception(proc.communicate()[0])
            except:
                pass
            proc.terminate()
            raise

        proc.terminate()

def read_until(port, terminators=None, size=None):
    """\
    Read until any of the termination sequences is found ('\n' by default), the size
    is exceeded or until timeout occurs.
    """
    if not terminators:
        terminators = ['\n']
    terms = map(lambda t: (t, len(t)), terminators)
    line = bytearray()
    timeout = Timeout(port._timeout)
    while True:
        c = port.read(1)
        if c:
            line += c
            for (terminator, lenterm) in terms:
                if line[-lenterm:] == terminator:
                    # break does not work here because it will only step out of for
                    return bytes(line)
            if size is not None and len(line) >= size:
                break
        else:
            break
        if timeout.expired():
            break
    return bytes(line)
