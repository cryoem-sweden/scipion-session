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

if n < 2 or n > 3:
    error("\n>>> Usage: \n"
          "       update_counter.py --fix\n"
          "       update_counter.py KEY counter_value")

if n == 2:

    if sys.argv[1] != '--fix':
        error("Only --fix is allowed as single argument")
    for k, c in counters.items():
        suffix = 'cem/%s_' % k if k.startswith('cem') else '%s/%s' % (k, k)
        pattern = '/data/staging/' + suffix + '%05d' 
	folder = pattern % c
        existing = False
        print("Checking %s" % k)
        while os.path.exists(folder):
            existing = True
            print("Existing %s, searching..." % folder)
            c += 1
            folder = pattern % c
        if existing:
            print("New counter: %d" % c)
            counters[k] = c

else:
    key = sys.argv[1]
    value = int(sys.argv[2])

    if not key in counters:
        error("Key '%s' not found" % key)
    # Update specific counter with provided value
    counters[key] = value
    
print("Writing counters")
sessionsSet.counters.set(counters)
sessionsSet.write()
sessionsSet.close()
print("Done")



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

