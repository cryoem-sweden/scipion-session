"""
This module contains classes and utility functions to deal with users
that can book the microscope and can start a session.
"""

import csv
import datetime as dt
from base import DataObject, parseCsv


class Reservation(DataObject):
    # List of attributes that will be set as UString
    ATTR_STR = ['username', 'resource', 'title', 'begin', 'end', 'reference']

    def _getDate(self, attrName):
        value = self.getAttributeValue(attrName)
        month, day = value.strip().split()[1].split('/')
        now = dt.datetime.now()
        return dt.datetime(year=now.year, month=int(month), day=int(day))

    def beginDate(self):
        return self._getDate('begin')

    def endDate(self):
        return self._getData('end')

    def isToday(self):
        return self.sameDay(dt.datetime.now())

    def sameDay(self, date):
        return self.beginDate() == dt.datetime(year=date.year, month=date.month,
                                               day=date.day)


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


