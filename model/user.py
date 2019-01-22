"""
This module contains classes and utility functions to deal with users
that can book the microscope and can start a session.
"""
from __future__ import print_function
import json

from base import DataObject
from config import STAFF


class User(DataObject):
    ATTR_STR = ['email', 'userName', 'firstName', 'lastName',
                'phone', 'group', 'lab', 'bookedId']

    def __init__(self, **kwargs):
        DataObject.__init__(self, **kwargs)
        self._account = None
        self._piAccount = None
        self._isStaff = False

    def getEmail(self):
        return self.email.get()

    def getFullName(self):
        return '%s %s' % (self.firstName, self.lastName)

    def getGroup(self):
        return self.group.get().lower()

    def getUserName(self):
        return self.userName.get()

    def isStaff(self):
        """ Users that are Facility staff. """
        return self.getGroup() == 'fac'

    def isUserStaff(self):
        """ Facility staff that work with users. """
        return self.getEmail() in STAFF

    def getLab(self):
        return self.lab.get()

    def getId(self):
        return self.bookedId.get()

    def inPortal(self):
        """ Return True if this user from the Booking system is
        also registered in the Portal.
        """
        return self._account is not None

    def inPortalPi(self):
        return self._piAccount is not None

    def getAccount(self):
        """ Return the account json dict (from Portal). """
        return self._account

    def getPiAccount(self):
        return self._piAccount

    def setAccount(self, accountJson):
        self._account = accountJson

    def setPiAccount(self, accountJson):
        self._piAccount = accountJson

    def isPi(self):
        """ Return True if this user is PI (info from portal). """
        return self._account['pi'] if self.inPortal() else False

    def getPiEmail(self):
        return self._piAccount['email'] if self.inPortalPi() else ''

    def getPiName(self):
        return self._piAccount['name'] if self.inPortalPi() else ''


def loadUsersFromJsonFile(usersJsonFn):
    users = None
    with open(usersJsonFn) as jsonFile:
        users = loadUsersFromJson(json.load(jsonFile)['users'])

    return users


def userFromBookedJson(u):
    organization = u['organization']
    if organization:
        parts = u['organization'].split()
        group = parts[0]
        lab = parts[1] if len(parts) > 1 else ''
    else:
        print("Unknown organization for Booking System user: %s %s"
              % (u['firstName'], u['lastName']))
        group = ''
        lab = ''

    return User(email=u['emailAddress'],
                userName=u['userName'],
                firstName=u['firstName'],
                lastName=u['lastName'],
                phone=u['phoneNumber'],
                group=group,
                lab=lab,
                bookedId=u['id'])


def userFromAccountJson(a):
    return User(email=a['email'],
                userName=a['email'],
                firstName=a['first_name'],
                lastName=a['last_name'],
                phone=None,
                group='',
                lab='',
                bookedId=None)


SPECIAL_EMAILS = ['nick@twinkletoessoftware.com',
                  'lujorent@gmail.com']


def _specialUser(u):
    """ Return True for some special users that should be ignored.
    """
    return u['emailAddress'] in SPECIAL_EMAILS


def loadUsersFromJson(usersJson):
    """ This will load users from the json retrieved from the
    booking system.
    """
    return [userFromBookedJson(u) for u in usersJson if not _specialUser(u)]


def printUsers(users):
    """ Print the list of users. """
    headers = ["Name", "Email", "Phone", "Group", "In Portal", "PI"]
    row_format = u"{:<30}{:<35}{:<15}{:<15}{:<10}{:<10}"

    print(row_format.format(*headers))

    for u in users:
        print(row_format.format(
            u.getFullName(),
            u.getEmail(),
            u.phone.get(),
            u.group.get(),
            'Yes' if u.inPortal() else 'No',
            u.getPiName()
            ))