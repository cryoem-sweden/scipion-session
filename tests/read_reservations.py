
import sys
import datetime as dt

from model.data import findReservationFromDate





def parseDate(dateStr):
    """ Get date from YYYY/MM/DD string """
    year, month, day = dateStr.split('/')
    return dt.datetime(year=int(year), month=int(month), day=int(day))

if __name__ == "__main__":
    date = parseDate(sys.argv[1]) if len(sys.argv) > 1 else dt.datetime.now()
    resource = sys.argv[2] if len(sys.argv) > 2 else None

    r = findReservationFromDate(date, resource)

    if r is None:
        print "No reservation found. "
    else:
        r.printAll()