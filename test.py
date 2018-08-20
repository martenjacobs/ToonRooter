import unittest
import rooter
import StringIO
import os
import tempfile
import base64

class FakeSerial(object):
    def __init__(self):
        self.input = StringIO.StringIO()
        self.output = StringIO.StringIO()
        self._timeout = 10

    def readline(self):
        return self.input.readline()

    def read(self, amount):
        return self.input.read(amount)

    def reset_input_buffer(self):
        self.input.close()
        self.input = StringIO.StringIO()

    def write(self, content):
        self.output.write(content)

    def flush(self):
        pass

    def read_until(self, terminator):
        rooter.read_until(self, [terminator])

class TestRooter(unittest.TestCase):

    def setUp(self):
        self.port = FakeSerial()
        self.rooter = rooter.Rooter(**{
            "port": self.port,
            "ssh_pubkey_data": "my_pubkey",
            "has_jtag": True,
            "check_uboot": True,
            "cleanup_payload": True,
            "reboot_after": True,
            "boot_only": False,
            "jtag_hardware": "rpi3"
        })
        pass

    def tearDown(self):
        pass

    def test_read_uboot_version(self):
        #read_uboot_version(self)
        pass

    def test_access_uboot(self):
        #access_uboot(self, password)
        pass

    def test_patch_uboot(self):
        #patch_uboot(self)
        pass

    def test_create_payload_tar(self):
        import tarfile
        tar_path = self.rooter.create_payload_tar()
        self.assertTrue(tarfile.is_tarfile(tar_path))

    def test_write_payload(self):
        content = "Lorem ipsum dolor sit amet"
        tmp_path = tempfile.mkstemp(suffix=".tar.gz")[1]
        with open(tmp_path, "w") as f:
            f.write(content)

        self.port.input.write("Testing... / # ")
        self.rooter.write_payload(tmp_path)
        written = self.port.output.getvalue()
        lines = written.split('\n')
        self.assertEqual(len(lines), 3)
        (cmd, b64content, terminator) = lines
        self.assertEqual(cmd, 'base64 -d | tar zxf -')
        self.assertEqual(base64.b64decode(b64content), content)
        self.assertEqual(terminator, '\x04')

    def test_patch_toon(self):
        #patch_toon(self)
        pass

    def test_start_bootloader(self):
        #start_bootloader(self, bin_path)
        pass

if __name__ == '__main__':
    unittest.main()
