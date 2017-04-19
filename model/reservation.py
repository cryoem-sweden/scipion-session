"""
This module contains classes and utility functions to deal with users
that can book the microscope and can start a session.
"""

import re
import datetime as dt
from base import DataObject, parseCsv

CEM_REGEX = re.compile("(cem\d{5})")


class Reservation(DataObject):
    # List of attributes that will be set as UString
    ATTR_STR = ['username', 'resource', 'title', 'begin', 'end', 'reference']

    def __init__(self, **kwargs):
        DataObject.__init__(self, **kwargs)
        # Lets check if this reservation is for a national project
        # by parsing the title and checking for a cemXXXXX code
        # both cem and CEM will be recognized
        t = self.title.get().lower()
        m = CEM_REGEX.search(t)
        self.cemCode = None if m is None else m.groups()[0]
        self._beginDate = self._getDate('begin')
        self._endDate = self._getDate('end')

    def _getDate(self, attrName):
        value = self.getAttributeValue(attrName)
        month, day = value.strip().split()[1].split('/')
        now = dt.datetime.now()
        return dt.datetime(year=now.year, month=int(month), day=int(day))

    def beginDate(self):
        return self._beginDate

    def endDate(self):
        return self._endDate

    def isActiveToday(self):
        return self.isActiveOnDay(dt.datetime.now())

    def isActiveOnDay(self, date):
        day = dt.datetime(year=date.year, month=date.month, day=date.day)
        return self.beginDate() >= day and self.endDate() <= day

    def isActiveOnMonth(self, month):
        return self.beginDate().month == month or self.endDate().month == month

    def getCemCode(self):
        return self.cemCode

    def isNationalFacility(self):
        return self.getCemCode() is None


def loadReservations(reservationsCsvFile='data/reservations.csv'):
    """ Load a list of order objects from a given json file.
    """
    dataFile = open(reservationsCsvFile)

    # We assume that the header line contains the following string
    headerString = '"User","Resource","Title","Description","Begin","End"'

    reservations = []

    for row in parseCsv(reservationsCsvFile):
        # Remove weird code form the name part
        username = row[0].replace('{title} {resourcename}', '')
        reservations.append(Reservation(username=username.strip(),
                                        resource=row[1],
                                        title=row[2],
                                        begin=row[4],
                                        end=row[5],
                                        reference=row[9]))
        #for i, p in enumerate(row):
        #    print "%02d: %s" % (i, p)

    return reservations


