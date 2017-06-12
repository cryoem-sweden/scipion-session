
import os
import json

from model.reservation import BookingManager, loadReservationsFromJson

import pyworkflow.object as pwobj
import pyworkflow.utils as pwutils


if __name__ == "__main__":
    # Assume the data folder is in the same place as this script
    dataFolder = os.path.join(os.path.dirname(__file__), '../data')
    # Load username and password for booked system
    bMan = BookingManager()
    rJson = bMan.fetchReservationsJson('%s/booked-user.json' % dataFolder)

    rPath = '%s/reservations.json' % dataFolder

    with open(rPath, 'w') as rFile:
        json.dump(rJson, rFile)

    reservations = loadReservationsFromJson(rJson)

    rSqlite = '%s/test-reservations.sqlite' % dataFolder
    pwutils.cleanPath(rSqlite)

    s = pwobj.Set(filename=rSqlite)
    for r in reservations:
        s.append(r)


    s.write()


