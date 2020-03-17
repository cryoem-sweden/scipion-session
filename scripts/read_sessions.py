from __future__ import print_function

import sys
from collections import OrderedDict
import datetime as sessionDt

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

def parseDate(dateStr):
    """ Get date from YYYY/MM/DD string """
    year, month, day = dateStr.split('/')
    return sessionDt.datetime(year=int(year), month=int(month), day=int(day))

fromDate = parseDate(sys.argv[1])
toDate = parseDate(sys.argv[2])


def _filterSession(session):
    #return session.getId().startswith('cem00258')
    return True
    return session.pi.getName().startswith('Jens')


for session in sessionsSet:
    if _filterSession(session):
        microscope = session.getMicroscope()
        dateStr = session.getObjCreation()
        sessionDt = session.getObjCreationAsDate()
        date = sessionDt.date()

        if fromDate <= sessionDt <= toDate:
            # If there are duplicates (same day, same microscope) we will keep the last one
            s = session.clone()
            s.setObjCreation(dateStr)
            if date not in dates[microscope]:
                dates[microscope][date] = [s]
            else:
                dates[microscope][date].append(s)

piDict = {}

for mic, micDict in dates.iteritems():
    print("\n>>>> Microscope: ", mic)
    for date, sessionList in micDict.iteritems():
        for session in sessionList:
            pi = session.pi
            user = session.user
            row = (session.getObjCreation(),
                   session.getId(),
                   pi.getName(),
                   user.getName(), user.getEmail()
                   )
            print(row_format.format(*row))

            # ------- Group users by PI --------------
            if not pi.getEmail() in piDict:
                piDict[pi.getEmail()] = (pi, session.getId()[:8], [])

            _, _, piUsers = piDict[pi.getEmail()]
            if not any(u.getEmail() == user.getEmail() for u in piUsers):
                piUsers.append(user)

    print("Sessions: ", len(micDict))
    values = list(piDict.values())
    values.sort(key=lambda tuple: tuple[1])

    lastCem = None
    for pi, cem, piUsers in values:
        if lastCem != cem:
            print("\nCEM: %s" % cem)
            lastCem = cem
        print(pi.getName(), pi.getEmail())

        for u in piUsers:
            print("   -", u.getName(), u.getEmail())
