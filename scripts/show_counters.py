
import sys
import json
from collections import OrderedDict
import functools

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

def cmpKey(key1, key2):
    if key1 == key2:
        return 0
    l1, l2 = len(key1), len(key2)
    if l1 == l2:
        return -1 if key1 < key2 else 1
    return -1 if l1 < l2 else 1

if '--as-params' in sys.argv:
    params = []
    keys = sorted(counters.keys())
    for k in keys:
        v = counters[k]
        params.append({"label": k, "value": v})
    form = {"params": params}
    print(json.dumps(form, indent=4))
else:
    pwutils.prettyDict(counters)


