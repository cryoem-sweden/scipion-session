
import os

import pyworkflow.object as pwobj
import pyworkflow.utils as pwutils

from base import DataObject
from user import User
from order import Order
from reservation import Reservation



class Session(DataObject):
    pass


class SessionManager():
    def __init__(self, filename=None):

        fileExists = os.path.exists(filename)
        self._allSets = {}

        def _createSet(prefix):
            s = pwobj.Set(filename, prefix)
            if fileExists:
                s.loadAllProperties()
                s.enableAppend()
            self._allSets[prefix] = s
            return s

        self._users = _createSet('User')
        self._orders = _createSet('Order')
        self._reservations = _createSet('Reservation')
        self._sessions = _createSet('Session')

    def getUsers(self):
        return self._users

    def getOrders(self):
        return self._orders

    def getReservations(self):
        return self._reservations

    def getSessions(self):
        return self._sessions

    def commit(self):
        for s in self._allSets.values():
            s.write()


