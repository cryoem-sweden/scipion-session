"""
This module contains classes and utility functions to deal with users
that can book the microscope and can start a session.
"""

import re
import datetime as dt
import json
import requests

from base import DataObject, parseCsv

CEM_REGEX = re.compile("(cem\d{5})")


class Reservation(DataObject):
    # List of attributes that will be set as UString
    ATTR_STR = ['username', 'resource', 'title', 'begin', 'end', 'reference',
                'userId', 'resourceId']

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
        # Sample datetime: 2017-06-06T21:00:00+0000
        year, month, day = value.strip().split('T')[0].split('-')
        return dt.datetime(year=int(year), month=int(month), day=int(day))

    def beginDate(self):
        return self._beginDate

    def endDate(self):
        return self._endDate

    def getDuration(self):
        return self.endDate() - self.beginDate()

    def isActiveToday(self):
        return self.isActiveOnDay(dt.datetime.now())

    def isActiveOnDay(self, date):
        day = dt.datetime(year=date.year, month=date.month, day=date.day)
        return self.beginDate() <= day and self.endDate() >= day

    def isActiveOnMonth(self, month):
        return self.beginDate().month == month or self.endDate().month == month

    def startsOnDay(self, date):
        day = dt.datetime(year=date.year, month=date.month, day=date.day)
        return self.beginDate() == day

    def startsToday(self):
        return self.startsOnDay(dt.datetime.now())

    def getCemCode(self):
        return self.cemCode

    def isNationalFacility(self):
        return self.getCemCode() is not None


def loadReservations(reservationsFile='data/reservations.json'):
    """ Load a list of order objects from a given json file.
    """
    dataFile = open(reservationsFile)
    return loadReservationsFromJson(json.load(dataFile))


def loadReservationsFromJson(dataJson):
    reservations = []

    for item in dataJson['reservations']:
        # Remove weird code form the name part
        username = '%s %s' % (item['firstName'], item['lastName'])
        reservations.append(Reservation(username=username,
                                        resource=item['resourceName'],
                                        resourceId=item['resourceId'],
                                        title=item['title'],
                                        begin=item['startDate'],
                                        end=item['endDate'],
                                        reference=item['referenceNumber'],
                                        userId=item['userId']
                                        ))
    return reservations


class BookingManager():
    """ Helper class to interact with the booking system.
    """
    BASE_URL = 'http://cryoem-sverige.bookedscheduler.com/Web/Services/index.php/'

    def getUrl(self, suffix):
        return self.BASE_URL + suffix

    def login(self, userJson):
        """ Login the given user.
        Params:
            userJson: input json dict with the username and password.
        Returns:
            A dict with headers required for next operations.
        """
        url = self.getUrl('Authentication/Authenticate')
        response = requests.post(url, data=json.dumps(userJson))

        if response.status_code != 200:
            print("Error", response.status_code)
            return None
        else:
            rJson = response.json()
            # Return headers needed for any further operation
            return {'userId': rJson['userId'],
                    'sessionToken': rJson['sessionToken']
                    }

    def getHeaders(self, userToken):
        return {'X-Booked-UserId': userToken['userId'],
                'X-Booked-SessionToken': userToken['sessionToken']
                }

    def getReservations(self, headers):
        """ Retrieve the reservations, given the user credentials in header. """
        url = self.getUrl('Reservations/')
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print("Error", response.status_code)
            return None
        else:
            rJson = response.json()
            # Return headers needed for any further operation
            return rJson

    def logout(self, userToken):
        url = self.getUrl('Authentication/SignOut')
        response = requests.post(url, data=json.dumps(userToken))
        if response.status_code != 200:
            print("Error", response.status_code)
        else:
            print("Session closed.")

    def fetchReservationsJson(self, userJsonFileName):
        """ Retrieve the reservations from the booking system using the
        credentials of the given user.
         (in a json file {"username": "pp", "password": "kk"} )
        """
        with open(userJsonFileName) as userFile:
            userJson = json.load(userFile)
            # userToken should be a dict containing
            # 'userId' and 'sessionToken' keys
            userToken = self.login(userJson)
            headers = self.getHeaders(userToken)
            return self.getReservations(headers)

        return None
