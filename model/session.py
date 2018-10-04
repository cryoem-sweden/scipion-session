
import os

from pyworkflow.object import *
import pyworkflow.utils as pwutils

from base import DataObject, UString, JsonDict, Person
from user import User
from order import Order
from reservation import Reservation



class Session(DataObject):
    def __init__(self, **kwargs):
        DataObject.__init__(self, **kwargs)
        self.userId = Integer()  # From the booking system
        self.sessionCode = UString()  # if non-empty, it is a national project
        self.isNational = Boolean()  # True is it is a national project
        self.user = Person()
        self.pi = Person()
        self.visitor = Person()
        self.microscope = String()  # microscope alias
        self.microscopeSettings = JsonDict()  # store a json dict
        self.invoice = JsonDict()  # json dict with 'reference' and 'address'
        self.dataFolder = UString()  # where data is being stored
        self.scipionProjectName = UString()  # scipion project folder
        self.endDate = UString()  # store end date of the session


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

    def getSessionFromCode(self, sessionCode):
        """ Retrieve the session correspoding to this code. """
        for s in self._sessions:
            if s.sessionCode == sessionCode:
                return s.clone()

        return None

    def updateSession(self, session):
        self._sessions.enableAppend()
        self._sessions.update(session)
        self._sessions.write()

