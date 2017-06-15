
import os
import json

import pyworkflow.object as pwobj
import pyworkflow.utils as pwutils

from model.datasource.booking import BookingManager
from model.datasource.portal import PortalManager
from model.reservation import loadReservationsFromJson
from model.user import mergeUsersAccounts
from model.session import SessionManager



if __name__ == "__main__":
    # Assume the data folder is in the same place as this script
    dataFolder = os.path.join(os.path.dirname(__file__), '../data')
    # Load username and password for booked system
    t = pwutils.Timer()

    t.tic()
    bMan = BookingManager()
    bookedUserFn = '%s/booked-user.json' % dataFolder
    uJson = bMan.fetchUsersJson(bookedUserFn)
    bookedUsersListFn = '%s/booked-users-list.json' % dataFolder
    with open(bookedUsersListFn, 'w') as usersFile:
        json.dump(uJson, usersFile, indent=2)

    t.toc()

    print 'Users: ', len(uJson['users'])

    # Fetch orders from the Portal
    # pMan = PortalManager('data/portal-api.json')
    #
    # accountsJson = pMan.fetchAccountsJson()
    # print "Accounts: ", len(accountsJson['items'])
    # accountsFile = open('data/test-portal-accounts.json', 'w')
    # json.dump(accountsJson, accountsFile, indent=2)
    # accountsFile.close()

