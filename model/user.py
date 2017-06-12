"""
This module contains classes and utility functions to deal with users
that can book the microscope and can start a session.
"""

import json

from base import DataObject, parseCsv


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


def loadUsersFromJson(usersJson):
    """ This will load users from the json retrieved from the
    booking system.
    """
    users = []
    for u in usersJson:
        users.append(User(email=u['emailAddress'],
                          userName=u['userName'],
                          firstName=u['firstName'],
                          lastName=u['lastName'],
                          phone=u['phoneNumber'],
                          group=u['organization'],
                          bookedId=u['id']))

    return users


