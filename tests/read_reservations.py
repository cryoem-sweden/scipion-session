
import sys
import datetime as dt
import argparse

from model.data import Data


def parseDate(dateStr):
    """ Get date from YYYY/MM/DD string """
    year, month, day = dateStr.split('/')
    return dt.datetime(year=int(year), month=int(month), day=int(day))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Query reservations. ")
    add = parser.add_argument  # shortcut
    add('--microscope', help="Select microscope")
    add('--day', help="Date to check for reservations (Today by default)")
    add('--month', help="Check all reservations of this month")
    args = parser.parse_args()

    d = Data(microscope=args.microscope)

    if args.month:
        reservations = d.findReservations(
            lambda r: r.beginDate().month == date.month)
    else: # day
        date = parseDate(args.day) if args.day else dt.datetime.now()
        reservations = d.findReservationFromDate(date, resource=args.microscope)


    if reservations:
        for r in reservations:
            r.printAll()
    else:
        print "No reservation found. "
