import serial
import logging
import re
import telnetlib
import os
import subprocess
from time import sleep

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

def root(path, openocd_addr=None):
    port=serial.Serial(
        port=path,
        baudrate=115200
    )
    do_root(port, openocd_addr)

def do_root(port, has_jtag):
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
    elif has_jtag is False:
        log.error("Unable to log in using password, need a JTAG debugger")
        return
    else:
        log.info("Loading new bootloader")
        start_bootloader(has_jtag, "u-boot.bin")
        port.reset_input_buffer()
        do_root(port, None)


def access_uboot(port, password):
    port.write(password)
    port.flush()
    log.info("Logged in to uboot")
    pass

def start_bootloader(has_jtag, bin_path):

    log.info("Starting openocd")

    proc = subprocess.Popen(['openocd', '-s', '/usr/share/openocd', '-f', 'raspberrypi.cfg', '-f', 'ed20.cfg'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        wait = 10
        log.info("Waiting for {} seconds".format(wait))
        sleep(wait)
        client = telnetlib.Telnet('localhost', 4444)
        log.debug(client.read_until("> "))
        client.write("soft_reset_halt\n")
        log.debug(client.read_until("> "))
        sleep(0.1)
        client.write("reset halt\n")
        log.debug(client.read_until("> "))
        sleep(0.1)
        client.write("load_image {} 0xa1f00000\n".format(bin_path))
        log.debug(client.read_until("> "))
        sleep(0.1)
        client.write("resume 0xa1f00000\n")
    except:
        try:
            log.exception(proc.communicate()[0])
        except:
            pass
        proc.terminate()
        raise

    proc.terminate()

def read_uboot_version(port):
    version_line_match = re.compile(r'U-Boot ([^ ]+)')
    while True:
        line = port.readline().strip()
        match = version_line_match.match(line)
        if match:
            return match.group(1)
