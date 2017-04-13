"""
This module contains classes and utility functions to deal with users
that can book the microscope and can start a session.
"""

from base import DataObject, UString


class User(DataObject):
    # List of attributes that will be set as UString
    ATTR_STR = ['email', 'name', 'username']


def loadUsers(usersCsvFile='data/users.csv'):
    """ Load a list of order objects from a given json file.
    """
    dataFile = open(usersCsvFile)

    # We assume that the header line contains the following string
    headerString = 'Username,Email,Phone,Organization,Position,Created'

    users = []

    for line in dataFile:
        if headerString in line:
            continue
        # Values should be separated by comma
        parts = line.split(',')
        # Remove weird code form the name part
        name = parts[0].replace('{title} {resourcename}', '')
        users.append(User(name=name.strip(),
                          username=parts[1].strip(),
                          email=parts[2].strip()))

    dataFile.close()

    return users


