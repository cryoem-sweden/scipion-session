
import os
import json

import pyworkflow.object as pwobj
import pyworkflow.utils as pwutils

from model.datasource.booking import BookingManager
from model.reservation import loadReservationsFromJson
from model.user import loadUsersFromJson
from model.session import SessionManager



if __name__ == "__main__":
    # Assume the data folder is in the same place as this script
    dataFolder = os.path.join(os.path.dirname(__file__), '../data')
    # Load username and password for booked system
    t = pwutils.Timer()

    t.tic()
    bMan = BookingManager()
    bookedUserFn = '%s/booked-user.json' % dataFolder
    rJson = bMan.fetchReservationsJson(bookedUserFn)
    uJson = bMan.fetchUsersJson(bookedUserFn)
    t.toc()

    rPath = '%s/reservations.json' % dataFolder
    with open(rPath, 'w') as rFile:
        json.dump(rJson, rFile)
    reservations = loadReservationsFromJson(rJson)
    print "Reservations: ", len(reservations)

    uPath = '%s/test-booked-users.json' % dataFolder
    with open(uPath, 'w') as rFile:
        json.dump(uJson, rFile)
    users = loadUsersFromJson(uJson['users'])
    print 'Users: ', len(users)


    rSqlite = '%s/test-sessions.sqlite' % dataFolder
    pwutils.cleanPath(rSqlite)

    s = SessionManager(filename=rSqlite)
    rList = s.getReservations()

    for r in reservations:
        rList.append(r)

    uList = s.getUsers()
    for u in users:
        uList.append(u)


    rList.write()
    uList.write()

