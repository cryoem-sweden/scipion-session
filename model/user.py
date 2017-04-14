"""
This module contains classes and utility functions to deal with users
that can book the microscope and can start a session.
"""

from base import DataObject, parseCsv


class User(DataObject):
    # List of attributes that will be set as UString
    ATTR_STR = ['email', 'name', 'username', 'phone', 'group']


def loadUsers(usersCsvFile='data/users.csv'):
    """ Load a list of order objects from a given json file.
    """
    dataFile = open(usersCsvFile)

    # We assume that the header line contains the following string
    headerString = 'Username,Email,Phone,Organization,Position,Created'

    users = []

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


