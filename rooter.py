import serial
import logging
import re
import telnetlib
import os
import subprocess
import tarfile
import base64
from time import sleep
from serial.serialutil import Timeout

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

def root(path, has_jtag=False, no_check_uboot=False):
    port=serial.Serial(
        port=path,
        baudrate=115200
    )
    do_root(port, has_jtag, no_check_uboot)
    log.info("Your Toon is now rooted. Please wait for it to boot up and try to log in using SSH")

def do_root(port, has_jtag=False, no_check_uboot=False):
    if not no_check_uboot:
        uboot_passwords={
            "2010.09-R6" : "f4E9J",
            "2010.09-R8" : "3BHf2",
            "2010.09"    : "toon"
        }
        uboot_version=read_uboot_version(port)
        log.info("Toon has U-Boot version {}".format(uboot_version))
        if uboot_version in uboot_passwords:
            log.info("Using password to log in")
            access_uboot(port, uboot_passwords[uboot_version])
            patch_uboot(port)
            log.info("Waiting for boot up")
            write_payload(port)
            patch_toon(port)
            return
        elif has_jtag is False:
            log.error("Unable to log in using password (need a JTAG debugger, but it's disabled)")
            return
    if has_jtag:
        log.info("Loading new bootloader")
        start_bootloader("u-boot.bin")
        port.reset_input_buffer()
        do_root(port, True)
    else:
        log.error("Need JTAG when rooting without manual reset")
        return




def read_uboot_version(port):
    version_line_match = re.compile(r'^U-Boot ([^ ]+)')
    while True:
        line = port.readline().strip()
        match = version_line_match.match(line)
        if match:
            return match.group(1)

def access_uboot(port, password):
    log.info("Logging in to U-Boot")
    port.write(password)
    port.flush()
    log.debug(port.read_until("U-Boot>"))
    log.debug("Logged in to U-Boot")

def patch_uboot(port):
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

def write_payload(port):

    tar_path = 'payload.tar.gz'

    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add('payload/', arcname='payload')


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

def patch_toon(port):
    log.info("Patching Toon")
    log.debug(port.read_until("/ # "))
    port.write("sh payload/patch_toon.sh\n")
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
    log.info("Cleaning up")
    port.write("rm -r payload\n")
    log.debug(port.read_until("/ # "))
    port.write("/etc/init.d/reboot\n")

def start_bootloader(bin_path):

    log.info("Starting openocd")

    proc = subprocess.Popen(['openocd', '-s', '/usr/share/openocd', '-f', 'raspberrypi.cfg', '-f', 'ed20.cfg'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

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
