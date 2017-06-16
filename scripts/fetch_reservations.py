
import os
import json

import pyworkflow.object as pwobj
import pyworkflow.utils as pwutils

from config import *
from model.datasource.booking import BookingManager
from model.reservation import loadReservationsFromJson
from model.user import loadUsersFromJson
from model.session import SessionManager


if __name__ == "__main__":

    # Load username and password for booked system
    t = pwutils.Timer()

    t.tic()
    bMan = BookingManager()
    bookedUserFn = getDataFile(BOOKED_LOGIN_USER)
    rJson = bMan.fetchReservationsJson(bookedUserFn)
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


