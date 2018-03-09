# ToonRooter

## What it does
This application roots your Toon from a Raspberry Pi.

At the moment, the following is implemented:
 - Detection of the U-Boot version
 - Loading of modified U-Boot version using JTAG
 - Logging in to supported versions of U-Boot
 - Setting up the U-Boot environment so the Toon boots into a serial console
 - Install and set up dropbear and sftp-server to let root user log in using an ssh key
 - Modify the firewall settings to enable remote access to ssh and http server
 - Generate SSH keys or let the user supply their own

### What it might do in the more distant future
 - Check the output from a few commands so we know if we're successful...
 - More fine-grained control of the installation package

## How safe is it?

I don't know.

You'll probably be fine. We're not overwriting the bootloader or important parts
of the OS, so I don't see it really breaking anything, but you should make sure all wires are connected
correctly, because otherwise you might short out something and break your Pi, Toon or both. If you are
having issues with your Toon, run this application again with the `--boot_only` flag set. When it's finished
you should be able to access a serial console on the Toon and check out what's wrong. To find some
'usual suspects', look through `payload/patch_toon.sh`, which is the script that's actually run on the Toon
to enable SSH access. The rest of the application basically just opens an injection vector to make that
possible.

## How to use it?

Make sure there's no power going in to either of the devices, and double check the connections
before powering up again.
Connect your Toon's debugging header to a Raspberry Pi according to the following pin assignments:

| Toon | Signal | Pi   |
|:----:|:------:|:----:|
|  1   |  RTCK  |      |
|  2   |  TRST  |  24  |
|  3   |  GND   |  25  |
|  4   |  TCK   |  23  |
|  5   |  GND   |  20  |
|  6   |  TMS   |  22  |
|  7   |  SRST  |  18  |
|  8   |  TDI   |  19  |
|  9   |  Vt    |      |
|  10  |  TDO   |  21  |
|  11  |  RxD   |  8   |
|  12  |        |      |
|  13  |  TxD   |  10  |
|  14  |  GND   |  9   |


Then make sure the serial port on the Pi is enabled and the serial console is disabled
using `raspi_config` and reboot if necessary. Install the dependencies mentioned in the
[Dependencies](#dependencies)-section.

Then get and run this application:
```bash
git clone https://github.com/martenjacobs/ToonRooter.git
cd ToonRooter
sudo python . --jtag-available
```

Then reset your Toon and let the magic happen :)

## Command line arguments

```
usage: sudo python . [-h] [--serial-port PATH] [--ssh-public-key PATH]
                  [--output-ssh-key PATH] [--private-key-password PASSWORD]
                  [--output-level INFO|DEBUG] [--jtag-available]
                  [--dont-check-uboot] [--dont-cleanup_payload]
                  [--dont-reboot_after] [--boot-only]

Root your Toon.

optional arguments:
  -h, --help            show this help message and exit
  --serial-port PATH    The path of the serial port to use
  --ssh-public-key PATH
                        The path to an RSA public key which should be an
                        allowed key on the Toon after rooting it. If not
                        supplied, a key pair is generated
  --output-ssh-key PATH
                        The path to output a generated key pair (the public
                        key will have a .pub suffix). Default is to write
                        id_rsa and id_rsa.pub in the current directory.
                        Ignored if you've used --ssh-public-key
  --private-key-password PASSWORD
                        The password that should be used to encrypt the
                        private key when it's generated. Default is to use no
                        encryption. Ignored if you've used --ssh-public-key
  --output-level INFO|DEBUG
                        The level of output to print to the console
  --jtag-available      Indicates you have your Pi connected to your Toon's
                        JTAG headers
  --dont-check-uboot    Don't check whether we can access the installer
                        version of U-Boot before using JTAG to start up the
                        custom one.
  --dont-cleanup_payload
                        Leave the payload in /payload. Use this if you want to
                        include more files and do something with them.
  --dont-reboot_after   Don't reboot the Toon after rooting it. Use this if
                        you want to use the serial console after rooting
  --boot-only           Don't install the payload, just boot into the serial
                        console
```

## Dependencies

- Python 2.7

- OpenOCD from git (for newer Toons) (see [instructions](#install-openocd))

## Install OpenOCD
If your Toon has a newer U-Boot version than 2010-R8, a JTAG interface is required to
upload a bootloader that we have access to through the serial console. To do this,
you need to build a version of OpenOCD (at the time of writing the version in apt
doesn't support using the Pi's headers as JTAG debugger).

```bash
git clone --recursive git://git.code.sf.net/p/openocd/code openocd
cd openocd
./bootstrap
./configure --enable-sysfsgpio\
     --enable-bcm2835gpio \
     --enable-maintainer-mode \
     --disable-werror \
     --enable-ft2232_libftdi \
     --enable-ep93xx \
     --enable-at91rm9200 \
     --enable-usbprog \
     --enable-presto_libftdi \
     --enable-jlink \
     --enable-vsllink \
     --enable-rlink \
     --enable-arm-jtag-ew \
     --enable-dummy \
     --enable-buspirate \
     --enable-ulink \
     --enable-presto_libftdi \
     --enable-usb_blaster_libftdi \
     --enable-ft2232_libftdi\
     --prefix=/usr\
make -j4
sudo make install
```
> these instructions were based on the instructions posted [here](https://www.domoticaforum.eu/viewtopic.php?f=87&t=11230&start=210#p83745) by rboers

## Thanks
This application is based on instructions and software written by:
- marcelr
- klaphekje
- rboers
- other [domoticaforum.eu](https://www.domoticaforum.eu/viewforum.php?f=87) users
