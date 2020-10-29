
import os

from pyworkflow.object import *

from model.base import DataObject, UString, JsonDict, Person


class Session(DataObject):
    def __init__(self, **kwargs):
        DataObject.__init__(self, **kwargs)

        # The unique ID for this session
        # All national sessions will be cemXXXXX_YYYYY
        # where YYYYY is the count within that CEM
        # Other groups (sll, dbb, fac) will be groupYYYYY
        self.sessionId = UString(kwargs.get('id', None))

        self.pi = kwargs.get('pi', Person())
        self.user = kwargs.get('user', Person())
        self.operator = kwargs.get('operator', Person())

        # Store some info about the booking reservation:
        # userId, reservationId, duration, etc
        self._booking = JsonDict()
        self._microscope = JsonDict()  # store a json dict

        self.path = UString()  # Store the location of the Session data
        self.scipion = UString()  # Store the name of the Scipion project

        self.endDate = UString()  # store end date of the session

    def setId(self, group, counter):
        """ Set the session id based on the group and the counter. """
        g = group.lower()
        idFormat = '%s_%05d' if g.startswith('cem') else '%s%05d'
        self.sessionId.set(idFormat % (g, int(counter)))

    def getId(self):
        return self.sessionId.get()

    def getGroupCounter(self):
        id = self.getId()

        if self.isNational():
            group, counter = id.split('_')
        else:
            group = id[:3]
            counter = id[3:]

        return group, int(counter)

    def isNational(self):
        return self.getId().startswith('cem')

    def getCem(self):
        return self.getId().split('_')[0] if self.isNational() else None

    def setMicroscopeDict(self, **kwargs):
        self._microscope.set(kwargs)

    def getCamera(self):
        return self._microscope.get()['camera']

    def getMicroscope(self):
        return self._microscope.get()['microscope']

    def getPath(self, *paths):
        return os.path.join(self.path.get(), *paths)

    def setPath(self, path):
        self.path.set(path)

    def getScipionProjectName(self):
        return self.scipion.get()

    def setScipionProjectName(self, projName):
        self.scipion.set(projName)

    def getScipionProjectPath(self):
        return self.getPath(self.getScipionProjectName())

    def getStartDate(self):
        return self.getObj


class SessionSet(Set):
    ITEM_TYPE = Session

    def __init__(self, *args, **kwargs):
        Set.__init__(self, *args, **kwargs)
        self.counters = JsonDict({})


class SessionManager:
    def __init__(self, filename=None):

        fileExists = os.path.exists(filename)
        self._allSets = {}

        def _createSet(prefix):
            s = SessionSet(filename, prefix, classesDict=globals())
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
        # Update counter
        group, counter = session.getGroupCounter()
        countersDict = self._sessions.counters.get()
        countersDict[group.lower()] = counter + 1
        self._sessions.counters.set(countersDict)
        self._sessions.write()

    def getSessionFromCode(self, sessionCode):
        """ Retrieve the session corresponding to this code. """
        for s in self._sessions:
            if s.sessionCode == sessionCode:
                return s.clone()

        return None

    def updateSession(self, session):
        self._sessions.enableAppend()
        self._sessions.update(session)
        self._sessions.write()

    def getNextId(self, group):
        """ Return the next id of this group based on
        the existing counters. If the group is not there,
        the id will be 1.
        """
        countersDict = self._sessions.counters.get()
        return countersDict.get(group.lower(), 1)


def printSessions(sessions):
    headers = ["Date", "SessionId", "Microscope", "PI Name",
               "User Name", "User Email"]
    row_format = u"{:<25}{:<20}{:<15}{:<20}{:<20}{:<25}"
    print(row_format.format(*headers))

    for session in sessions:
        row = (str(session.date),
               session.getId(),
               session.getMicroscope(),
               session.pi.getName(),
               session.user.getName(), session.user.getEmail()
               )
        print(row_format.format(*row))
