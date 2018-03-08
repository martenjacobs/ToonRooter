import logging

logging.basicConfig(level=logging.INFO)

import rooter

rooter.root("/dev/serial0", True)
