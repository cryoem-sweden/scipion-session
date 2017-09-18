
import os
import json

import pyworkflow.utils as pwutils

from model.datasource.booking import BookingManager
from model.user import loadUsersFromJson
from config import *



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

    with open(getDataFile(LABS_FILE)) as labsJsonFile:
        labInfo = json.load(labsJsonFile)

    users = loadUsersFromJson(uJson['users'])
    # Validate users' organization is well formed
    for u in users:
        group = u.getGroup()
        groupParts = group.split()
        groupName = groupParts[0].lower()

        if u.getGroup() not in USER_GROUPS:
            print "ERROR: Wrong group name"
            u.printAll()

        if u.getGroup() in ['dbb', 'sll'] and not u.getLab() in labInfo:
            print "ERROR: Wrong lab name"
            u.printAll()


    # Fetch orders from the Portal
    # pMan = PortalManager('data/portal-api.json')
    #
    # accountsJson = pMan.fetchAccountsJson()
    # print "Accounts: ", len(accountsJson['items'])
    # accountsFile = open('data/test-portal-accounts.json', 'w')
    # json.dump(accountsJson, accountsFile, indent=2)
    # accountsFile.close()

