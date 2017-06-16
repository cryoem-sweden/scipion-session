
import os

from pyworkflow.object import *
import pyworkflow.utils as pwutils

from base import DataObject, UString, JsonDict
from user import User
from order import Order
from reservation import Reservation


class Person(DataObject):
    """ Simple class to hold name and email values. """
    ATTR_STR = ['email', 'name']


class Session(DataObject):
    def __init__(self, **kwargs):
        DataObject.__init__(self, **kwargs)
        self.userId = Integer() # From the booking system
        self.cemCode = UString()  # if non-empty, it is a national project
        self.user = Person()
        self.pi = Person()
        self.visitor = Person()
        self.microscopeSettings = JsonDict()  # store a json dict
        self.invoice = JsonDict()  # json dict with 'reference' and 'address'
        self.dataFolder = UString() # where data is being stored
        self.scipionProjectName = UString() # scipion project folder


class SessionManager():
    def __init__(self, filename=None):

        fileExists = os.path.exists(filename)
        self._allSets = {}

        def _createSet(prefix):
            s = Set(filename, prefix, classesDict=globals())
            if fileExists:
                s.loadAllProperties()
                if not s.isEmpty():
                    s.enableAppend()
            self._allSets[prefix] = s
            return s

        self._sessions = _createSet('Session')

    def getSessions(self):
        return self._sessions

    def storeSession(self, session):
        self._sessions.append(session)
        self._sessions.write()

