# -*- coding: utf-8 -*-
"""
This module contains classes and utility functions to deal with users
that can book the microscope and can start a session.
"""

import os
import re
import datetime as dt
import json
import requests

import pyworkflow.utils as pwutis

from base import DataObject, parseCsv
from datasource.booking import BookingManager


CEM_REGEX = re.compile("cem(\d+)")


class Reservation(DataObject):
    # List of attributes that will be set as UString
    ATTR_STR = ['username', 'resource', 'title', 'begin', 'end', 'reference',
                'userId', 'resourceId']

    def __init__(self, **kwargs):
        DataObject.__init__(self, **kwargs)
        self._beginDate = self._getDate('begin')
        self._endDate = self._getDate('end')
        # Lets check if this reservation is for a national project
        # by parsing the title and checking for a cemXXXXX code
        # both cem and CEM will be recognized
        t = self.title.get().lower()
        m = CEM_REGEX.search(t)
        if m is None:
            self.cemCode = None
        else:
            digits = m.groups()[0]
            if len(digits) > 5:
                print("WARNING: Wrong number of digits for CEM code in: ",
                      self.title.get())
            self.cemCode = "cem%05d" % int(digits)

    def _getDate(self, attrName):
        value = self.getAttributeValue(attrName)
        # Sample datetime: 2017-06-06T21:00:00+0000
        date, time = value.strip().split('T')
        year, month, day = date.split('-')
        hour = time.split(':')[0]
        return dt.datetime(year=int(year), month=int(month), day=int(day),
                           hour=int(hour))

    def beginDate(self):
        return self._beginDate

    def endDate(self):
        return self._endDate

    def getDuration(self):
        return self.endDate() - self.beginDate()

    def getTotalDays(self):
        """ Check the number of days (even partial) of the reservation. """
        d = self.getDuration()
        return d.days + (1 if d.seconds//3600 > 0 else 0)

    def _getDay(self, date):
        """ Return the datetime without hour. """
        return dt.datetime(year=date.year, month=date.month, day=date.day)

    def isActiveToday(self):
        return self.isActiveOnDay(dt.datetime.now())

    def isActiveOnDay(self, date):
        day = self._getDay(date)
        return (self._getDay(self.beginDate()) <= day and
                self._getDay(self.endDate()) >= day)

    def isActiveOnMonth(self, month):
        return self.beginDate().month == month or self.endDate().month == month

    def startsOnDay(self, date):
        day = self._getDay(date)
        return self._getDay(self.beginDate()) == day

    def startsToday(self):
        return self.startsOnDay(dt.datetime.now())

    def getCemCode(self):
        return self.cemCode

    def isNationalFacility(self):
        return self.getCemCode() is not None

    def isDowntime(self):
        t = self.title.get().lower()
        return ('cycle' in t or 'down' in t or 'fei' in t or 'maintenance' in t)


def loadReservations(userJsonFn, reservationsJsonFn, fromDate, toDate,
                     fetchData=True):
    """ Load reservation list either from the booking system or from a
    local json file with cached data.
    Params:
        userJsonFn: user credentials to login into the booking system
        reservationsJsonFile: local file to use in case the reservations can
        not be load from the booking system.
        fromDate-toDate: date range to retrieve reservations
    """
    if fetchData:
        try:
            bMan = BookingManager()
            print("Loading reservations from booking system...")

            t = pwutis.Timer()
            t.tic()
            reservationsJson = bMan.fetchReservationsJson(userJsonFn,
                                                          fromDate, toDate)
            if reservationsJson is None:
                raise Exception("Could not fetch data from the booking system.")
            t.toc()
            with open(reservationsJsonFn, 'w') as reservationsFile:
                json.dump(reservationsJson, reservationsFile)
        except Exception as ex:
            print("Error: ", ex)
            print("Trying to load reservations from file:", reservationsJsonFn)

    jsonFile = open(reservationsJsonFn)
    reservationsJson = json.load(jsonFile)
    jsonFile.close()

    return loadReservationsFromJson(reservationsJson)


def loadReservationsFromFile(reservationsJsonFile):
    """ Load a list of order objects from a given json file.
        """
    dataFile = open(reservationsJsonFile)
    reservations = loadReservationsFromJson(json.load(dataFile))
    dataFile.close()
    return reservations


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

def loadReservationsFromCsv(csvFile):
    """
    Parse reservations from CSV file from the Booking system with the following format:
Column:  0,      1,    2,         3,      4,      5,            6,                7,     8,           9,          10,    11,       12,
"Resource","Begin","End","Duration","Hours","Title","Description","Reference Number","User","First Name","Last Name","Email","Created","Last Modified","Status","Check In Time","Check Out Time","Original End",

"Talos Arctica","9/30/17 9:00 AM","10/1/17 11:00 PM","1 days 14 hours","38","CRYO CYCLE","","58f0a2ca644f7908614935","Marta Carroni","Marta","Carroni","marta.carroni@scilifelab.se","4/14/17 12:22 PM","","Created","","","",
"Titan Krios","10/1/17 9:00 AM","10/1/17 11:00 PM","14 hours","14","CRYO CYCLE and K2 BAKING","","58f0a024efe72490488767","Marta Carroni","Marta","Carroni","marta.carroni@scilifelab.se","8/17/17 3:59 PM","","Created","","","10/1/17 11:00 PM",
"Talos Arctica","10/2/17 9:00 AM","10/2/17 10:00 AM","1 hours","1","AlexM","AlexM","59a993571c159469569353","Alexander Mühleip","Alexander","Mühleip","alexander.muhleip@scilife","9/1/17 7:05 PM","","Created","","","",
"Titan Krios","10/4/17 9:00 AM","10/4/17 10:00 AM","1 hours","1","AlexM","AlexM","59bfb79e874d7730204368","Alexander Mühleip","Alexander","Mühleip","alexander.muhleip@scilife","9/18/17 2:10 PM","","Created","","","",
"Titan Krios","10/6/17 9:00 AM","10/7/17 6:00 PM","1 days 9 hours","33","","","59ca4628c0fee536094330","Shintaro Aibara","Shintaro","Aibara","shintaro.aibara@scilifelab.se","9/26/17 2:20 PM","","Created","","","",
"Titan Krios","10/9/17 9:00 AM","10/10/17 10:00 PM","1 days 13 hours","37","facility (replacement user lost)","","59a931550676b975035949","Julian Conrad","Julian","Conrad","julian.conrad@scilifelab.se","9/1/17 12:07 PM","10/19/17 4:54 PM","Created","","","10/9/17 5:00 PM",
    """
    reservations = []

    def _convertDateStr(inputDateStr):
        """ Convert the input data str from the csv report in the booking
        system to the one expected in the json format
        '06/06/17 9:00 PM' -> '2017-06-06T21:00:00+0000'
        """
        date, hour, m = inputDateStr.split()
        month, day, year = map(int, date.split('/'))
        h = int(hour.split(':')[0])
        if m == 'PM':
            h += 12

        return "20%d-%02d-%02dT%02d:00:00+0000" % (year, month, day, h)

    for row in parseCsv(csvFile):
        reservations.append(Reservation(username=row[8],
                                        resource=row[0],
                                        resourceId=-1, # no resource id in csv
                                        title=row[5],
                                        begin=_convertDateStr(row[1]),
                                        end=_convertDateStr(row[2]),
                                        reference=row[7],
                                        userId=-1
                                        ))
    return reservations


def printReservations(reservations):
    """ Print a list of reservations with a nice format. """
    headers = ["Start date", "End date", "Days", "Label", "Resource", "User Name", "Group"]
    row_format = u"{:<15}{:<15}{:<5}{:<10}{:<10}{:<35}{:<15}"
    print(row_format.format(*headers))

    totalDays = 0
    totalDaysDowntime = 0
    lastMonth = None

    for r in reservations:
        days = r.getTotalDays()

        begin = r.beginDate()
        if begin.month != lastMonth:
            print("Month: ", begin.month)
            lastMonth = begin.month

        label = ''

        if r.isDowntime():
            totalDaysDowntime += days
            label = 'downtime'
        else:
            totalDays += days

        if r.isNationalFacility():
            group = r.getCemCode()
        else:
            if r.user.isStaff():
                group = 'facility'
            else:
                group = 'sll' if 'scilifelab' in r.user.getEmail() else 'dbb'
                if not r.user.isPi() and not r.user.inPortalPi():
                    group += '(no pi)'

        row = (str(begin.date()),
               str(r.endDate().date()),
               days, label,
               r.resource.get().split()[0],
               r.user.getEmail(),
               group)

        print(row_format.format(*row))

    print("Total days: ", totalDays)
    print("Downtime: ", totalDaysDowntime)

