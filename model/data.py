
import os
import datetime as dt
import json

from config import *
from order import loadOrders
from reservation import BookingManager, loadReservationsFromJson
from user import loadUsers


class Data():
    def __init__(self, **kwargs):
        self.dataFolder = kwargs['dataFolder']
        self.microscope = kwargs.get('microscope', None)

        usersFn = self.getDataFile('users.csv')
        self._users = loadUsers(usersFn)
        self._usersDict = {}

        for u in self._users:
            self._usersDict[u.email.get()] = u
            u.isStaff = self._isUserStaff(u)

        # Try to read the reservations from the booking system
        # in case of a failure, try to read from cached-file
        reservationsFn = self.getDataFile('reservations.json')
        userJsonFn = self.getDataFile('booked-user.json')
        try:
            bMan = BookingManager()
            print "Loading reservations from booking system..."
            from pyworkflow.utils import Timer
            t = Timer()
            t.tic()
            reservationsJson = bMan.fetchReservationsJson(userJsonFn)
            t.toc()
            with open(reservationsFn, 'w') as reservationsFile:
                json.dump(reservationsJson, reservationsFile)
        except:
            print "Loading reservations from: ", reservationsFn
            reservationsJson = json.load(open(reservationsFn))

        self._reservations = loadReservationsFromJson(reservationsJson)
        print "Loaded reservations: ", len(self._reservations)

        ordersFn = self.getDataFile('orders_detailed.json')
        self._orders = loadOrders(ordersFn)

        self._accepted = []
        self._ordersDict = {}

        for o in self._orders:
            self._ordersDict[o.getId()] = o

            if o.status == 'accepted':
                self._accepted.append(o)

        # Keep a configuration of user, project-type and project
        self.user = None
        self.projectType = None
        self.projectId = None
        self.group = None
        self.cemCode = None

        self.now = dt.datetime.now()
        todayReservations = self.findReservationFromDate(self.now,
                                                         self.microscope)

        if todayReservations:
            n = len(todayReservations)
            # If there are more than one reservation (probably some overlapping
            # in the booking system), take the first one that starts today
            r = todayReservations[0]
            print "n: ", n
            if n > 1:
                for tr in todayReservations:
                    if tr.startsToday():
                        r = tr
                        break

            self._selectedReservation = r
            if r.user is not None:
                self.selectUser(r.user)
                # For staff users we will try to determine if the project
                # is internal or national facility
                if self.user.isStaff:
                    self.cemCode = r.getCemCode()
                    # Set the project type to either internal or national facility
                    projType = PROJECT_TYPES[1 if self.cemCode is None else 0]
                    self.selectProjectType(projType)
        else:
            print "No reservation found today for '%s'" % self.microscope

    def getDataFile(self, filename):
        return os.path.join(self.dataFolder, filename)

    def getReservations(self):
        return self._reservations

    def getOrder(self, cemCode):
        return self._ordersDict[cemCode.lower()]

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

    def getSelectedReservation(self):
        return self._selectedReservation

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
        return [o.getId() for o in self._accepted]

    def getScipionProject(self):
        now = self.now
        return '%s_scipion_%04d%02d%02d' % (self.getProjectId(),
                                            now.year, now.month, now.day)


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
        def _active(r):
            return r.isActiveOnDay(date) and (resource is None or
                                              r.resource == resource)
        return self.findReservations(_active)

    def findReservations(self, conditionFunc):
        """ Find reservations that satisfies the conditionFunc.
        The corresponding users will be set.
        """
        reservations = []

        for r in self._reservations:
            if conditionFunc(r):
                user = self.findUserFromReservation(r)
                r.user = user
                reservations.append(r)

        return reservations