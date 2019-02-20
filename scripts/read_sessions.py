from __future__ import print_function

from collections import OrderedDict

import pyworkflow as pw
from model.session import SessionManager
from config import *

from model.base import JsonDict


dataFn = getDataFile(SESSIONS_FILE)

sMan = SessionManager(dataFn)

sessionsSet = sMan.getSessions()
# sessionsSet.enableAppend()
sessions = [s.clone() for s in sessionsSet]

#
# for session in sessions:
#     session.printAll()
    #session.microscopeSettings.set({"a": 1})
    #sessionsSet.update(session)
# sessionsSet.counters = JsonDict({'sll': 154,
#                                  'dbb': 125,
#                                  'fac': 88
#                                  })
#
# sessionsSet.write()

headers = ["Date", "SessionId", "PI Name", "User Name", "User Email"]
row_format = u"{:<25}{:<20}{:<25}{:<25}{:<25}"
print(row_format.format(*headers))

filterMic = 'Talos Arctica'
#filterMic = 'Titan Krios'

dates = {'Talos Arctica': OrderedDict(),
         'Titan Krios': OrderedDict()
         }


def _filterSession(session):
    return session.getId().startswith('cem00258')


for session in sessionsSet:
    if _filterSession(session):
        microscope = session.getMicroscope()
        dateStr = session.getObjCreation()
        dt = session.getObjCreationAsDate()
        date = dt.date()

        # If there are duplicates (same day, same microscope) we will keep the last one
        s = session.clone()
        s.setObjCreation(dateStr)
        dates[microscope][date] = s

for mic, micDict in dates.iteritems():
    print("\n>>>> Microscope: ", mic)
    for date, session in micDict.iteritems():
        row = (session.getObjCreation(),
               session.getId(),
               session.pi.getName(),
               session.user.getName(), session.user.getEmail()
               )
        print(row_format.format(*row))

    print("Sessions: ", len(micDict))
