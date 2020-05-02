from __future__ import print_function

import sys

from model.user import printUsers
from model.data import Data
from config import *


if __name__ == "__main__":
    showAll = '--all' in sys.argv
    csv = '--csv' in sys.argv

    data = Data(dataFolder=getDataFile())
    users = data.getUsers()

    def _noInPortal(u):
        return not u.inPortal()

    def _noPiInPortal(u):
        return u.inPortal() and not u.isPi() and not u.getGroup() == 'fac' and not u.inPortalPi()

    def _noSe(u):
        return not u.getEmail().endswith('.se')

    users.sort(key=lambda u: u.getFullName())

    if showAll:
        printUsers(users, csv=csv)
    else:
        print("\n\n>>> NOT IN PORTAL >>>")
        printUsers(filter(_noInPortal, users), csv=csv)

        print("\n\n>>> PI not IN PORTAL >>>")
        printUsers(filter(_noPiInPortal, users), csv=csv)

        print("\n\n>>> NOT .se EMAIL >>>")
        printUsers(filter(_noSe, users), csv=csv)

    print("Total: ", len(users))
