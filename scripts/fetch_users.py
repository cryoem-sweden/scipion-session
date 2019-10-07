from __future__ import print_function

import sys

from model.user import printUsers
from model.data import Data
from config import *


if __name__ == "__main__":
    noInPortal = '--no-portal' in sys.argv
    noPi = '--no-pi' in sys.argv
    noSe = '--no-se' in sys.argv

    data = Data(dataFolder=getDataFile())
    users = data.getUsers()

    def _noInPortal(u):
        return not u.inPortal()

    def _noPiInPortal(u):
        return u.inPortal() and not u.isPi() and not u.getGroup() == 'fac' and not u.inPortalPi()

    def _noSe(u):
        return not u.getEmail().endswith('.se')

    if noInPortal:
        users = filter(_noInPortal, users)

    if noPi:
        users = filter(_noPiInPortal, users)

    if noSe:
        users = filter(_noSe, users)

    users.sort(key=lambda u: u.getFullName())
    #printUsers(users)
    print("Total: ", len(users))
