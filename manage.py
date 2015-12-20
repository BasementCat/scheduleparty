import os
import sys
import bottle
import logging
from subprocess import call

import app
from app.lib.commands import run_command
from app.commands import *

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    run_command(sys.argv)
