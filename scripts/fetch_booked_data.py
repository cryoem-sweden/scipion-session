
import sy   s
import json
import datetime as dt

from config import *
from model.data import Data


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

    reservationList  = []
    for r in reservations:
        # print(b['startDate'], b['endDate'],
        #       '%s (%s)' % (b['resourceName'], b['resourceId']),
        #       b['title'],
        #       '%s %s (%s) ' % (b['firstName'], b['lastName'], b['userId']))

        reservationList.append({
            'startDate': r.beginDate().isoformat(),
            'endDate':  r.endDate().isoformat(),
            'title': r.title.get(),
            'resourceName': r.resource.get(),
            'user':   {'email': r.user.getEmail(),
                       'name': r.user.getFullName()
                       },
        })


    outputFn =  'data/booked-data.json'

    with  open(outputFn) as f:
        print("Writing reservations JSON to: %s" % outputFn)
        json.dump(reservationList, f)
