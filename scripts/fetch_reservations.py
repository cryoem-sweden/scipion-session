
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

    reservations = filter(lambda r: r.resource.get() == TALOS, reservations)
    printReservations(reservations)
    print "Reservations: ", len(reservations)


