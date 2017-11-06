
import os
import sys
import json
import datetime as dt

import pyworkflow.object as pwobj
import pyworkflow.utils as pwutils

from config import *
from model.datasource.booking import BookingManager
from model.reservation import loadReservationsFromJson
from model.user import loadUsersFromJson
from model.session import SessionManager


def parseDate(dateStr):
    """ Get date from YYYY/MM/DD string """
    year, month, day = dateStr.split('/')
    return dt.datetime(year=int(year), month=int(month), day=int(day))



if __name__ == "__main__":

    n = len(sys.argv)

    fromDate = parseDate(sys.argv[1]) if n > 1 else None
    toDate = parseDate(sys.argv[2]) if n > 2 else None

    # Load username and password for booked system
    t = pwutils.Timer()

    t.tic()
    bMan = BookingManager()
    bookedUserFn = getDataFile(BOOKED_LOGIN_USER)
    rJson = bMan.fetchReservationsJson(bookedUserFn,
                                       fromDate=fromDate, toDate=toDate)
    uJson = bMan.fetchUsersJson(bookedUserFn)
    t.toc()

    rPath = getDataFile(BOOKED_RESERVATIONS)
    with open(rPath, 'w') as rFile:
        json.dump(rJson, rFile)
    reservations = loadReservationsFromJson(rJson)
    print "Reservations: ", len(reservations)

    # uPath = '%s/test-booked-users.json' % dataFolder
    # with open(uPath, 'w') as rFile:
    #     json.dump(uJson, rFile)
    # users = loadUsersFromJson(uJson['users'])
    # print 'Users: ', len(users)


