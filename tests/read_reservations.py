
import sys
import datetime as dt

from model.data import Data


def parseDate(dateStr):
    """ Get date from YYYY/MM/DD string """
    year, month, day = dateStr.split('/')
    return dt.datetime(year=int(year), month=int(month), day=int(day))


if __name__ == "__main__":
    date = parseDate(sys.argv[1]) if len(sys.argv) > 1 else dt.datetime.now()
    resource = sys.argv[2] if len(sys.argv) > 2 else None

    d = Data(microscope=resource)
    reservations = d.findReservationFromDate(date, resource)

    if reservations:
        for r in reservations:
            r.printAll()
    else:
        print "No reservation found. "
