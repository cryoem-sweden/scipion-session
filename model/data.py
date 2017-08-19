
import os
import datetime as dt
import json

from config import *
from order import loadOrders
from reservation import loadReservations
from session import SessionManager, Session, Person
from user import loadUsersFromJsonFile
from datasource.portal import PortalManager


class Data():
    def __init__(self, **kwargs):
        self.dataFolder = kwargs['dataFolder']
        self.microscope = kwargs.get('microscope', None)
        self.now = dt.datetime.now()
        self.date = kwargs.get('date', self.now)
        print "Using day: ", self.date

        apiJsonFile = self.getDataFile(PORTAL_API)
        self.pMan = PortalManager(apiJsonFile)
        # Fetch orders from the Portal and write to a json file
        #users = self.pMan.fetchAccountsJson()

        sessionsFile = self.getDataFile(SESSIONS_FILE)
        self.sMan = SessionManager(sessionsFile)

        usersFn = self.getDataFile(BOOKED_USERS_LIST)
        self._users = loadUsersFromJsonFile(usersFn)
        self._usersDict = {}

        for u in self._users:
            self._usersDict[u.email.get()] = u
            u.isStaff = self._isUserStaff(u)

        with open(self.getDataFile(LABS_FILE)) as labsJsonFile:
            self._labInfo = json.load(labsJsonFile)

        # Try to read the reservations from the booking system
        # in case of a failure, try to read from cached-file
        reservationsFn = self.getDataFile(BOOKED_RESERVATIONS)
        userJsonFn = self.getDataFile(BOOKED_LOGIN_USER)
        self._reservations = loadReservations(userJsonFn, reservationsFn,
                                              self.date)
        print "Loaded reservations: ", len(self._reservations)

        ordersFn = self.getDataFile(PORTAL_ORDERS)
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

        todayReservations = self.findReservationFromDate(self.date,
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

    def loadOrderDetails(self):
        if self.isNational():
            self._orderJson = self.pMan.fetchOrderDetailsJson(self.cemCode)
        else:
            self._orderJson = None

    def getOrderDetails(self):
        return self._orderJson

    def _createSession(self, projPath, scipionProjName):
        s = Session()
        s.dataFolder.set(projPath)
        s.scipionProjectName.set(scipionProjName)

        u = self.getSelectedUser()
        s.userId.set(u.getId())
        s.user = Person(name=u.getFullName(), email=u.getEmail())
        s.sessionCode.set(self.projectId)
        s.isNational.set(self.isNational())
        s.microscope.set(self.microscope)

        if self.isNational():
            if self._orderJson is None:
                raise Exception("Could not retrieve order details for %s" %
                                self.cemCode)
            s.pi = Person(name=self._orderJson['fields']['project_pi'],
                          email=self._orderJson['fields']['pi_email'])
            address = self._orderJson['fields']['project_invoice_addess']
            s.invoice.set({'address': address})
        else:
            lab = u.getLab()
            if lab in self._labInfo:
                li = self._labInfo[lab]
                s.pi = Person(name=li['pi_name'], email=li['pi_email'])
                s.invoice.set({'address': li['invoice_address']})

        return s

    def storeSession(self, projPath, scipionProjName):
        s = self._createSession(projPath, scipionProjName)
        self.sMan.storeSession(s)

    def getDataFile(self, filename):
        return os.path.join(self.dataFolder, filename)

    def getReservations(self):
        return self._reservations

    def getOrder(self, cemCode):
        return self._ordersDict[cemCode.lower()]

    def _isUserStaff(self, user):
        return user.getEmail() in STAFF

    def getUserString(self, user):
        return "%s  --  %s" % (user.getFullName(), user.getEmail())

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
        return 'cem' if self.isNational() else self.user.getGroup()

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
        userId = reservation.userId.get()

        for u in self._users:
            if userId == u.bookedId.get():
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