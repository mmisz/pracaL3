#!/usr/bin/python3.6

import sys
import logging

logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,  '/home/epi/18_miszkurka/pracaL2/')
sys.path.insert(0, '/home/epi/18_miszkurka/pracaL2/portal_forum')

from portal_forum import create_app 
application = create_app() 
