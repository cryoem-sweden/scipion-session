
import os
import sys
import json
import datetime as dt

import pyworkflow.object as pwobj
import pyworkflow.utils as pwutils

from config import *
from model.data import Data
from model.reservation import loadReservationsFromJson, printReservations


def parseDate(dateStr):
    """ Get date from YYYY/MM/DD string """
    year, month, day = dateStr.split('/')
    return dt.datetime(year=int(year), month=int(month), day=int(day))


if __name__ == "__main__":

    n = len(sys.argv)

    fromDate = parseDate(sys.argv[1]) if n > 1 else None
    toDate = parseDate(sys.argv[2]) if n > 2 else None

    data = Data(dataFolder=getDataFile(), fromDate=fromDate, toDate=toDate)
    reservations = data.getReservations()

    def _filterReservation(r):
        isCEM = (r.isNationalFacility())
        return r.resource.get() in MICROSCOPES # and isCEM

    reservations = filter(_filterReservation, reservations)
    stats = {TITAN: {'cem': 0, 'fac': 0, 'sll': 0, 'dbb': 0, 'mmk': 0},
             TALOS: {'cem': 0, 'fac': 0, 'sll': 0, 'dbb': 0, 'mmk': 0}}

    wrongGroups = []

    for r in reservations:
        d = stats[r.resource.get()]
        group = r.user.getGroup()
        if r.isNationalFacility():
            d['cem'] += r.getTotalDays()
        else:
            if group not in d:
                wrongGroups.append((group, r.username.get()))
            else:
                d[group] += r.getTotalDays()

    printReservations(reservations)
    print("Reservations: %d" % len(reservations))

    pwutils.prettyDict(stats)

    if wrongGroups:
        print("ERROR: Wrong groups: ")
    for group, username in wrongGroups:
        print("   group: '%s', user: %s" % (group, username))


