from __future__ import print_function

import sys
from collections import OrderedDict

import pyworkflow as pw
import pyworkflow.utils as pwutils

from model.session import SessionManager
from config import *

from model.base import JsonDict


dataFn = getDataFile(SESSIONS_FILE)

sMan = SessionManager(dataFn)

sessionsSet = sMan.getSessions()
counters = sessionsSet.counters.get()

print("Counters: ")
pwutils.prettyDict(counters)

n = len(sys.argv)

def error(msg):
    print(msg)
    sys.exit(1)

if n != 3:
    error("Usage: update_counter.py KEY counter_value")

key = sys.argv[1]
value = int(sys.argv[2])

if not key in counters:
    error("Key '%s' not found" % key)

counters[key] = value
sessionsSet.counters.set(counters)
sessionsSet.write()
sessionsSet.close()

# sessionsSet.enableAppend()
# for session in sessions:
#     session.printAll()
    #session.microscopeSettings.set({"a": 1})
    #sessionsSet.update(session)
# sessionsSet.counters = JsonDict({'sll': 154,
#                                  'dbb': 125,
#                                  'fac': 88
#                                  })
#

