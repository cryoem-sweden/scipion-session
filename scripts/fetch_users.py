
import os
import json

import pyworkflow.utils as pwutils

from model.datasource.booking import BookingManager
from model.user import loadUsersFromJson
from model.datasource.portal import PortalManager
from model.order import loadAccountsFromJson
from config import *


def _getAccountsEmailSet():
    apiJsonFile = 'data/%s' % PORTAL_API
    pMan = PortalManager(apiJsonFile)
    # Fetch users from the Portal
    accounts = loadAccountsFromJson(pMan.fetchAccountsJson(), isPi=False)
    return set(u['email'] for u in accounts)


if __name__ == "__main__":
    # Assume the data folder is in the same place as this script
    dataFolder = os.path.join(os.path.dirname(__file__), '../data')
    # Load username and password for booked system
    t = pwutils.Timer()

    t.tic()
    bMan = BookingManager()
    bookedUserFn = getDataFile(BOOKED_LOGIN_USER)
    uJson = bMan.fetchUsersJson(bookedUserFn)
    bookedUsersListFn = getDataFile(BOOKED_USERS_LIST)
    with open(bookedUsersListFn, 'w') as usersFile:
        json.dump(uJson, usersFile, indent=2)

    t.toc()

    print 'Users: ', len(uJson['users'])

    accountsSet = _getAccountsEmailSet()

    headers = ["Name", "Email", "Phone", "Group", "In Portal"]
    row_format = u"{:<30}{:<35}{:<15}{:<20}{:<10}"
    print row_format.format(*headers)

    users = loadUsersFromJson(uJson['users'])
    # Validate users' organization is well formed
    for u in users:
        print(row_format.format(
            u.getFullName(),
            u.getEmail(),
            u.phone.get(),
            u.group.get(),
            'Yes' if u.getEmail() in accountsSet else 'No',
            ))

    #emails = [u.getEmail() for u in users]
    #print ",".join(emails)