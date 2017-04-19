
import os
import datetime as dt

from config import *
from order import loadOrders
from reservation import loadReservations
from user import loadUsers


class Data():
    def __init__(self, **kwargs):
        self.microscope = kwargs['microscope']

        self._users = loadUsers()
        self._usersDict = {}
        for u in self._users:
            self._usersDict[u.email.get()] = u
            u.isStaff = self._isUserStaff(u)

        self._reservations = loadReservations()

        self._orders = loadOrders()
        self._accepted = []
        for o in self._orders:
            if o.status == 'accepted':
                self._accepted.append(o)

        # Keep a configuration of user, project-type and project
        self.user = None
        self.projectType = None
        self.projectId = None
        self.group = None

        now = dt.datetime.now()
        todayReservations = self.findReservationFromDate(now, self.microscope)

        if todayReservations:
            r = todayReservations[0]
            self._selectedReservation = r
            self.selectUser(r.user)
            # For staff users we will try to determine if the project
            # is internal or national facility
            if self.user.isStaff:
                cemCode = r.getCemCode()
                # Set the project type to either internal or national facility
                projType = PROJECT_TYPES[0 if cemCode is None else 1]
                self.selectProjectType(projType)
        else:
            print "No reservation found today for '%s'" % self.microscope

    def _isUserStaff(self, user):
        return user.email.get() in STAFF

    def getUserString(self, user):
        return "%s  --  %s" % (user.name.get(), user.email.get())

    def getUserStringList(self):
        usList = []

        # Add stuff personnel first
        for email in STAFF:
            usList.append(self.getUserString(self._usersDict[email]))
        # Add other users
        for u in self._users:
            if u.email.get() not in STAFF:
                usList.append(self.getUserString(u))

        return usList

    def getUserFromStr(self, userStr):
        name, email = userStr.split('--')
        return self._usersDict[email.strip()]

    def selectUser(self, user):
        self.user = user
        if user.isStaff:
            self.projectType = None
        else:
            self.projectType = PROJECT_TYPES[1]
            self._loadProjectId()

    def getSelectedUser(self):
        return self.user

    def selectProjectType(self, projType):
        self.projectType = projType
        if not self.user.isStaff:
            raise Exception("Project type only can be selected for "
                            "STAFF users.")
        else:
            self._loadProjectId()

    def isNational(self):
        return self.projectType == PROJECT_TYPES[0]

    def getProjectType(self):
        return self.projectType

    def getProjectGroup(self):
        return 'cem' if self.isNational() else self.user.group.get()

    def getDataFolder(self):
        # Work around the 'int' folder prefix
        groupDataFolder = GROUP_DATA[self.getProjectGroup()]
        return os.path.join(DEFAULTS[DATA_FOLDER], groupDataFolder)

    def getProjectFolder(self):
        return os.path.join(self.getDataFolder(), self.getProjectId())

    def setProjectId(self, projId):
        self.projectId = projId

    def getProjectId(self):
        return self.projectId

    def _findNextProjectId(self):
        group = self.getProjectGroup()
        folder = self.getDataFolder()
        last = 0
        for d in os.listdir(folder):
            if os.path.isdir(os.path.join(folder, d)) and d.startswith(group):
                n = int(d.replace(group, ''))
                last = max(last, n)

        return '%s%05d' % (group, last+1)

    def _loadProjectId(self):
        if self.isNational():
            self.projectId = self.cemCode
        else:
            # Grab this from the log of sessions
            self.projectId = self._findNextProjectId()

    def getNationalProjects(self):
        return [o.name.get().lower() for o in self._accepted]

    def getScipionProject(self):
        return '%s_scipion' % self.getProjectId()

    def getScipionProjectFolder(self):
        return os.path.join(self.getProjectFolder(), self.getScipionProject())

    def findUserFromReservation(self, reservation):
        """ Find the user of the given reservation .
        """
        username = reservation.username.get()

        for u in self._users:
            if username in u.name.get():
                return u

        return None

    def findReservationFromDate(self, date, resource=None):
        """ Find the reservation of a given date and resource. """
        reservations = []

        for r in self._reservations:
            if (r.isActiveOnDay(date) and
                (resource is None or r.resource == resource)):
                user = self.findUserFromReservation(r)
                r.user = user
                reservations.append(r)

        return reservations

