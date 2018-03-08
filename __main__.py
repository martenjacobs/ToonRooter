import logging

logging.basicConfig(level=logging.INFO)

import rooter

logging.info("Waiting for Toon to restart")
rooter.root("/dev/serial0", True)
