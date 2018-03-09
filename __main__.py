import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

import rooter

log.info("Waiting for Toon to restart")
rooter.root("/dev/serial0", True, False)
