import rooter
import serial


port=serial.Serial(
        port='/dev/serial0',
        baudrate=115200
    )

port.write("\n")
port.flush()
rooter.write_payload(port)
rooter.patch_toon(port)
