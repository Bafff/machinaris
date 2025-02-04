#
# Optionally performs a blockchain database backup.
# Always performs a blockchain services stop/start as well.
#

import os
import subprocess

from api import app
from common.config import globals

def execute():
    chia_binary = globals.get_blockchain_binary(os.environ['blockchains'])
    # TODO Optionally perform a database backup with the blockchain stopped for consistency
    app.logger.info("Executing blockchain restart for {0}...".format(chia_binary))
    subprocess.call("{0} start farmer -r >/dev/null 2>&1".format(chia_binary), shell=True)
