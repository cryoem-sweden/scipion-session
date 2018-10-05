
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


if __name__ == "__main__":

    n = len(sys.argv)

    rPath = getDataFile(BOOKED_RESERVATIONS)
    with open(rPath) as f:
        rJson = json.load(f)

    reservations = sorted(loadReservationsFromJson(rJson), key=lambda r: r.beginDate())
    print "Reservations: ", len(reservations)

    headers = ["Start date", "Days", "Microscope", "Username", "CEM", "Title"]
    row_format = u"{:<13}{:<5}{:<20}{:<20}{:<10}{:<20}"
    print row_format.format(*headers)

    for r in reservations:
        resource = r.resource.get()
        if resource in MICROSCOPES:
            beginStr = r.begin.get().split('T')[0]
            cemStr = "" if r.getCemCode() is None else r.getCemCode()
            print row_format.format(beginStr, r.getTotalDays(),
                                    resource,
                                    r.username.get(),
                                    cemStr,
                                    r.title.get())


