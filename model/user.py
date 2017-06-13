"""
This module contains classes and utility functions to deal with users
that can book the microscope and can start a session.
"""

import json

import pyworkflow.object as pwobj
from base import DataObject, parseCsv, UString


class User(DataObject):
    # List of attributes that will be set as UString
    ATTR_STR = ['email', 'userName', 'firstName', 'lastName',
                'phone', 'group', 'bookedId']

    def getEmail(self):
        return self.email.get()

    def getFullName(self):
        return '%s %s' % (self.firstName, self.lastName)

    def getGroup(self):
        return self.group.get().lower()

    def getUserName(self):
        return self.userName.get()

    def isStaff(self):
        return getattr('piId', None) == -1


# TODO: Rename as loadUsersFromCsv
def loadUsers(usersCsvFile='data/users.csv'):
    """ Load a list of order objects from a given json file.
    """
    users = []
    dataFile = open(usersCsvFile)

    for row in parseCsv(usersCsvFile):
        # Remove weird code form the name part
        name = row[0].replace('{title} {resourcename}', '')
        users.append(User(name=name.strip(),
                          username=row[1].strip(),
                          email=row[2].strip(),
                          phone=row[3].strip(),
                          group=row[4].strip().lower()))

    dataFile.close()

    return users


def loadUsersFromJsonFile(usersJsonFn):
    users = None
    with open(usersJsonFn) as jsonFile:
        users = loadUsersFromJson(json.load(jsonFile)['users'])

    return users


def userFromBookedJson(u):
     return User(email=u['emailAddress'],
                  userName=u['userName'],
                  firstName=u['firstName'],
                  lastName=u['lastName'],
                  phone=u['phoneNumber'],
                  group=u['organization'],
                  bookedId=u['id'])


def userFromAccountJson(a):
    return User(email=a['email'],
                userName=a['email'],
                firstName=a['first_name'],
                lastName=a['last_name'],
                phone=None,
                group=None,
                bookedId=None)

def loadUsersFromJson(usersJson):
    """ This will load users from the json retrieved from the
    booking system.
    """
    return [userFromBookedJson(u) for u in usersJson]





def mergeUsersAccounts(usersJson, accountsJson):
    """ Merge users information from users in the booking system
    and Accounts in the portal system.
    """

    def _updateUserFromAccount(user, a):
        user.piId = pwobj.Integer(99999)
        user.invoiceReference = UString()
        user.invoiceAddress = UString()
        user.university = UString('UNKNOWN')

        # Fill in more information from the corresponding Account
        if a is not None:
            if a['pi']:
                user.piId.set(None)
                user.invoiceReference.set(a['invoice_ref'])
                user.invoiceAddress.set(json.dumps(a['invoice_address']))

            user.university = UString('UNKNOWN')

    accountsDict = {}
    for a in accountsJson:
        accountsDict[a['email']] = a

    users = []
    usersDict = {}
    for u in usersJson:
        email = u['emailAddress']
        usersDict[email] = u
        user = userFromBookedJson(u)

        a = accountsDict.get(email, None)
        _updateUserFromAccount(user, a)
        users.append(user)

    for a in accountsJson:
        email = a['email']

        if email not in usersDict:
            user = userFromAccountJson(a)
            _updateUserFromAccount(user, a)
            users.append(user)

    return users







