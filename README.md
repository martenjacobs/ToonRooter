# ToonRooter

## What it does
This application roots your Toon. *Well, like, sort of. It's not finished yet, but it will!*

## How?

Connect your Toon's debugging header to a Raspberry Pi according to the following pin assignments:

| Toon | Signal | Pi   |
|:----:|:------:|:----:|
|  1   |  RTCK  |      |
|  2   |  TRST  |  24  |
|  3   |  GND   |  20  |
|  4   |  TCK   |  23  |
|  5   |  GND   |  25  |
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
sudo python .
```

## Dependencies

- Python 2.7

- OpenOCD from git (for newer Toons) (see [instructions](#install-openocd))

## Install OpenOCD
If your Toon has a newer U-Boot version than 2010-R8, a JTAG interface is required to
upload a bootloader that we have access to through the serial console. To do this,
you need to build a version of OpenOCD (at the time of writing the version in apt is not
new enough).

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
