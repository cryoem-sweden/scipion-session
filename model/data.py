
import os
import datetime as dt
import json
import re
import sys
import codecs
from collections import OrderedDict

import pyworkflow.em as em
import pyworkflow.utils as pwutils
from pyworkflow.project import Manager

from config import *
from base import Person
from order import loadOrders, loadAccountsFromJson, loadActiveBags
from reservation import loadReservations, printReservations
from session import SessionManager, Session, printSessions
from user import loadUsersFromJsonFile, loadUsersFromJson, printUsers
from datasource.portal import PortalManager
from datasource.booking import BookingManager

PROJ_NATIONAL = 0
PROJ_INTERNAL = 1
PROJ_FACILITY = 2


class Data:
    def __init__(self, **kwargs):
        self.dataFolder = kwargs['dataFolder']
        self.microscope = kwargs.get('microscope', None)
        self.now = dt.datetime.now()
        self.error = ''

        if 'fromDate' in kwargs:
            self.fromDate = kwargs['fromDate']
            self.toDate = kwargs['toDate']
            self.date = self.fromDate
        else:
            self.date = kwargs.get('date', dt.datetime.now())
            week = dt.timedelta(days=7)
            # Retrieve reservations from one week before to one week later
            # of the current date
            self.fromDate = self.date - week
            self.toDate = self.date + week

        print "Using day: ", self.date
        self.pMan = PortalManager(self.getDataFile(PORTAL_API))
        self.sMan = SessionManager(self.getDataFile(SESSIONS_FILE))
        self.bMan = BookingManager()

        self._loadUsers()
        self._loadOrders()
        self._loadReservations()

        # Keep a configuration of user, project-type and project
        self.user = None
        self.projectType = None
        self.projectId = None
        self.group = None
        self.cemCode = None
        self.reservation = None

    def loadOrderDetails(self):
        if self.isNational():
            self._orderJson = self.pMan.fetchOrderDetailsJson(self.cemCode)
        else:
            self._orderJson = None

    def getOrderDetails(self, cemCode=None):
        """ Return the order details of from the given cemCode, if None
        return the current loaded order.
        """
        if cemCode is None:
            return self._orderJson

        return self.pMan.fetchOrderDetailsJson(cemCode)

    def getNowStr(self):
        return "%04d%02d%02d" % (self.now.year, self.now.month, self.now.day)

    def _loadUsers(self):
        """ Load users from Booking and match information with the portal. """
        print("Loading users......")

        bookedUserFn = getDataFile(BOOKED_LOGIN_USER)
        try:
            uJson = self.bMan.fetchUsersJson(bookedUserFn)
            bookedUsersListFn = getDataFile(BOOKED_USERS_LIST)
            with open(bookedUsersListFn, 'w') as usersFile:
                json.dump(uJson, usersFile, indent=2)
            self._users = loadUsersFromJson(uJson)
        except Exception as ex:
            self._users = loadUsersFromJsonFile(bookedUsersListFn)
        self._usersDict = {}

        for u in self._users:
            self._usersDict[u.getEmail()] = u
            self._usersDict[u.bookedId.get()] = u

        portalAccounts = self.getAccountsFromPortal()
        accountsDict = {a['email']: a for a in portalAccounts}

        noInPortal = []
        noPi = []

        for u in self._users:
            a = accountsDict.get(u.getEmail(), None)
            if a is None:
                noInPortal.append(u)
                piKey = PI_MAP.get(u.getEmail(), None)
            else:
                u.setAccount(a)
                piKey = a['invoice_ref']
                if u.isPi() or u.isStaff():
                    continue
                    # Try to check match the PI from Portal

            piA = accountsDict.get(piKey, None)
            if piA is None:
                if a is not None:  # Report problem only once
                    noPi.append(u)
            else:
                u.setPiAccount(piA)

        if noInPortal:
            print("\n>>>> Users NOT in PORTAL: ")
            printUsers(noInPortal)

        if noPi:
            print("\n>>>> Users NO PI: ")
            printUsers(noPi)

    def getUsers(self):
        return self._users

    def getUserString(self, user):
        return "%s  --  %s" % (user.getFullName(), user.getEmail())

    def getUserStringList(self):
        usList = []

        # Add stuff personnel first
        for email in STAFF:
            usList.append(self.getUserString(self._usersDict[email]))
        # Add other users
        for u in self._users:
            if not u.isStaff():
                usList.append(self.getUserString(u))

        return usList

    def getUserFromStr(self, userStr):
        name, email = userStr.split('--')
        return self._usersDict[email.strip()]

    def getAccountsFromPortal(self):
        return loadAccountsFromJson(self.pMan.fetchAccountsJson(),
                                    isPi=False, university=None)

    def _loadOrders(self):
        ordersFn = self.getDataFile(PORTAL_ORDERS)
        self._orders = loadOrders(ordersFn)

        print("Loaded orders: ", len(self._orders))

        self._accepted = []
        self._ordersDict = {}

        for o in self._orders:
            self._ordersDict[o.getId()] = o

            if o.status == 'accepted':
                self._accepted.append(o)

    def _loadReservations(self):
        # Try to read the reservations from the booking system
        # in case of a failure, try to read from cached-file
        reservationsFn = self.getDataFile(BOOKED_RESERVATIONS)
        userJsonFn = self.getDataFile(BOOKED_LOGIN_USER)
        useLocal = int(os.environ.get('SESSION_WIZARD_LOCAL', 0))

        try:
            self._reservations = loadReservations(userJsonFn, reservationsFn,
                                                  self.fromDate, self.toDate,
                                                  fetchData=not useLocal)
            # Load the user for each reservation
            for r in self._reservations:
                r.user = self._usersDict[r.userId.get()]

        except Exception as ex:
            self._reservations = []  # work even without reservations

        print("Loaded reservations: ", len(self._reservations))

        reservations = self.findReservationFromDate(self.date, self.microscope)
        if reservations:
            n = len(reservations)
            # If there are more than one reservation (probably some overlapping
            # in the booking system), take the first one that starts today
            r = reservations[0]
            print "n: ", n
            if n > 1:
                for tr in reservations:
                    if tr.startsToday():
                        r = tr
                        break

            self.reservation = r
        else:
            print "No reservation found today for '%s'" % self.microscope

    def getSessions(self):
        # Let's try to remove duplicated sessions here
        sessionDateMic = OrderedDict()
        duplicates = []
        noBooking = []

        for s in self.sMan.getSessions():
            sessionStartDate = s.getObjCreationAsDate()
            if (sessionStartDate < self.fromDate or
                sessionStartDate > self.toDate):
                continue
            session = s.clone()
            session.date = sessionStartDate
            session.reservation = None
            dateMic = (sessionStartDate.date(), s.getMicroscope())

            if dateMic in sessionDateMic:
                duplicates.append(sessionDateMic[dateMic])

            sessionDateMic[dateMic] = session

        sessions = list(sessionDateMic.values())

        for s in sessions:
            # We only need the reservation for internal sessions
            if not s.isNational():
                r = self.findReservationFromDate(s.date,
                                                 resource=s.getMicroscope(),
                                                 status='starts')
                if len(r) == 0:
                    print("ERROR: NO reservation found!!!")
                    print("     Date: %s, Microscope: %s" % (s.date, s.getMicroscope()))
                    print("     SessionID: %s" % s.getId())
                    noBooking.append(s)
                else:
                    if len(r) > 1:
                        print("WARNING: more than one reservation found!!!")
                        print("     Date: %s, Microscope: %s" % (s.date, s.getMicroscope()))
                        print("Taking first one...")
                    s.reservation = r[0]

        print("\n>>> DUPLICATED (IGNORED) SESSIONS: ")
        printSessions(duplicates)

        print("\n>>> SESSIONS WITH NO BOOKING (CHECK!!!)")
        printSessions(noBooking)

        return sessions


    def getDataFile(self, filename):
        return os.path.join(self.dataFolder, filename)

    def getResourceFile(self, filename):
        return os.path.join(self.dataFolder, 'resources', filename)

    def getReservations(self):
        return self._reservations

    def getOrder(self, cemCode):
        return self._ordersDict.get(cemCode.lower(), None)


    def findReservationFromDate(self, date, resource=None,
                                status='active'):
        """ Find the reservation of a given date and resource. """
        def _active(r):
            return r.isActiveOnDay(date) and (resource is None or
                                              r.resource == resource)

        def _starts(r):
            return r.startsOnDay(date) and (resource is None or
                                            r.resource == resource)

        return self.findReservations(_active if status is 'active' else _starts)

    def findReservations(self, conditionFunc):
        """ Find reservations that satisfies the conditionFunc.
        The corresponding users will be set.
        """
        reservations = []

        for r in self._reservations:
            if conditionFunc(r):
                reservations.append(r)

        return reservations

    def getActiveBags(self):
        return loadActiveBags(self.pMan)


    # ================== SESSION CREATION METHODS ===============================
    def createSession(self, microscope, camera, projectType,
                      cem=None, pi=None, user=None, operator=None,
                      preprocessing=None):
        # Update now variable
        self.now = dt.datetime.now()

        cem = cem.lower()

        if projectType == PROJ_NATIONAL:
            group = cem
        elif projectType == PROJ_FACILITY:
            group = 'fac'
        else:  # projectType == PROJ_INTERNAL:
            group = 'sll' if 'scilifelab' in pi.email.get() else 'dbb'

        session = Session()
        session.setId(group, counter=self.sMan.getNextId(group))
        session.setMicroscopeDict(microscope=microscope, camera=camera)

        # Take only the first 3 character for the data folder
        session.setPath(os.path.join(DEFAULTS[DATA_FOLDER], group[:3], session.getId()))
        if preprocessing == 'Scipion':
            session.setScipionProjectName('%s_scipion_%s'
                                          % (session.getId(),
                                             self.getNowStr()))
        if pi:
            session.pi = pi

        if user:
            session.user = user

        if operator:
            session.operator = operator

        return session

    def storeSession(self, session):
        self._createFolder(session.getPath())
        self._createSessionReadme(session)
        if session.getScipionProjectName():
            session.setScipionProjectName('%s_scipion_%s'
                                          % (session.getId(),
                                             self.getNowStr()))
            self._createSessionScipionProject(session)
        self.sMan.storeSession(session)

    def _createFolder(self, p):
        if os.path.exists(p):
            raise Exception("Path '%s' already exists.\n" % p)
        # Create the project path
        sys.stdout.write("Creating path '%s' ... " % p)
        pwutils.makePath(p)
        sys.stdout.write("DONE\n")

    def _createSessionReadme(self, session):
        """ Create the main data folder for this session and
        also the folder for Scipion pre-processing if required.
        Also create the README file inside the main folder.
        """
        # Write the README file
        readmeFn = session.getPath('README_%s.txt' % self.getNowStr())
        with codecs.open(readmeFn, "w", "utf-8") as f:
            #TODO: store some info from the reservation
            r = self.reservation

            def _writePerson(p, prefix):
                f.write("%s.name: %s\n" % (prefix, p.name))
                f.write("%s.email: %s\n" % (prefix, p.email))

            _writePerson(session.pi, 'pi')
            _writePerson(session.user, 'user')
            _writePerson(session.operator, 'operator')
            # Write title
            desc = "Not found" if r is None else r.title
            f.write("description: %s\n" % desc)

            f.write("date: %s\n" % self.getNowStr())

    def _getConfValue(self, key, default=''):
        return DEFAULTS.get(key, default)

    def _createSessionScipionProject(self, session):
        manager = Manager()
        projectPath = session.getScipionProjectPath()
        self._createFolder(projectPath)
        project = manager.createProject(session.getScipionProjectName(),
                                        location=projectPath)
        self.lastProt = None

        smtpServer = self._getConfValue(SMTP_SERVER, '')
        smtpFrom = self._getConfValue(SMTP_FROM, '')
        smtpTo = self._getConfValue(SMTP_TO, '')
        doMail = False
        doPublish = False

        microscope = session.getMicroscope()
        camera = session.getCamera()

        def getMicSetting(key):
            return MICROSCOPES_SETTINGS[microscope][key]

        cs = getMicSetting(CS)
        voltage = getMicSetting(VOLTAGE)
        # For now lets use only one GPU, the first in the list
        gpuId = str(getMicSetting(GPU)[0])

        isK2 = camera == K2
        pattern = CAMERA_SETTINGS[camera][PATTERN]

        # if camera == FALCON3:
        #     basePath = MIC_CAMERAS_SETTINGS[microscope][camera][MOVIES_FOLDER]
        #     filesPath = os.path.join(basePath, projId) + "_epu"
        # else:
        filesPath = session.getPath()

        protImport = project.newProtocol(em.ProtImportMovies,
                                         objLabel='Import movies',
                                         filesPath=filesPath,
                                         filesPattern=pattern,
                                         voltage=voltage,
                                         sphericalAberration=cs,
                                         samplingRate=None,
                                         magnification=None,
                                         dataStreaming=True,
                                         timeout=72000,
                                         inputIndividualFrames=False,
                                         stackFrames=False,
                                         writeMoviesInProject=True
                                         )

        # Should I publish html report?
        if doPublish == 1:
            publish = self._getConfValue('HTML_PUBLISH')
            #print("\n\nReport available at URL: %s/%s\n\n"
            #      %('http://scipion.cnb.csic.es/scipionbox',projName))
        else:
            publish = ''

        protMonitor = project.newProtocol(em.ProtMonitorSummary,
                                          objLabel='Summary Monitor',
                                          doMail=doMail,
                                          emailFrom=smtpFrom,
                                          emailTo=smtpTo,
                                          smtp=smtpServer,
                                          publishCmd=publish)

        def _saveProtocol(prot, movies=True, monitor=True):
            if movies:
                prot.inputMovies.set(self.lastProt)
                prot.inputMovies.setExtended('outputMovies')
            project.saveProtocol(prot)
            self.lastProt = prot
            if monitor:
                protMonitor.inputProtocols.append(prot)

        def _newProtocol(*args, **kwargs):
            return project.newProtocol(*args, **kwargs)

        _saveProtocol(protImport, movies=False)

        useMC = True
        useOF = False
        useSM = False
        useCTF = True
        useGCTF = True

        kwargs = {}

        protMC = None
        if useMC:
            # Create motioncorr
            from pyworkflow.em.packages.motioncorr import ProtMotionCorr
            protMC = _newProtocol(ProtMotionCorr,
                                 objLabel='Motioncorr',
                                 useMotioncor2=True,
                                 doComputeMicThumbnail=True,
                                 computeAllFramesAvg=True,
                                 gpuList=gpuId,
                                 extraProtocolParams='--use_worker_thread',
                                 **kwargs)
            _saveProtocol(protMC)

        if useOF:
            # Create Optical Flow protocol
            from pyworkflow.em.packages.xmipp3 import XmippProtOFAlignment

            protOF = _newProtocol(XmippProtOFAlignment,
                                 objLabel='Optical Flow',
                                 doSaveMovie=useSM,
                                 **kwargs)
            _saveProtocol(protOF)

        if useSM:
            from pyworkflow.em.packages.grigoriefflab import ProtSummovie
            protSM = _newProtocol(ProtSummovie,
                                 objLabel='Summovie',
                                 cleanInputMovies=useOF,
                                 numberOfThreads=1,
                                 **kwargs)
            _saveProtocol(protSM)

        lastBeforeCTF = self.lastProt
        lowRes, highRes = 0.03, 0.42

        protCTF = None
        if useCTF:
            from pyworkflow.em.packages.grigoriefflab import ProtCTFFind
            protCTF = _newProtocol(ProtCTFFind,
                                  objLabel='Ctffind',
                                  numberOfThreads=1,
                                  lowRes=lowRes, highRes=highRes)
            protCTF.inputMicrographs.set(lastBeforeCTF)
            protCTF.inputMicrographs.setExtended('outputMicrographs')
            _saveProtocol(protCTF, movies=False)

        if useGCTF:
            from pyworkflow.em.packages.gctf import ProtGctf
            protGCTF = _newProtocol(ProtGctf,
                                    objLabel='Gctf',
                                    lowRes=lowRes, highRes=highRes,
                                    windowSize=1024,
                                    maxDefocus=9.0,
                                    doEPA=False,
                                    doHighRes=True,
                                    gpuList=gpuId)
            protGCTF.inputMicrographs.set(lastBeforeCTF)
            protGCTF.inputMicrographs.setExtended('outputMicrographs')
            _saveProtocol(protGCTF, movies=False)
            protCTF = protGCTF

        project.saveProtocol(protMonitor)

        if protCTF is not None and protMC is not None:
            from pyworkflow.em.packages.xmipp3 import (XmippProtParticlePicking,
                                                       XmippParticlePickingAutomatic)
            # Include picking, extraction and 2D
            protPick1 = _newProtocol(XmippProtParticlePicking,
                                     objLabel='xmipp3 - supervised')
            protPick1.inputMicrographs.set(protMC)
            protPick1.inputMicrographs.setExtended('outputMicrographsDoseWeighted')
            _saveProtocol(protPick1, movies=False)

            protPick2 = _newProtocol(XmippParticlePickingAutomatic,
                                     objLabel='xmipp3 - supervised',
                                     streamingSleepOnWait=60,
                                     streamingBatchSize=0)
            protPick2.xmippParticlePicking.set(protPick1)
            _saveProtocol(protPick2, movies=False)

            from pyworkflow.em.packages.relion import (ProtRelionExtractParticles,
                                                       ProtRelionClassify2D)

            protExtract = _newProtocol(ProtRelionExtractParticles,
                                       objLabel='relion - extract particles',
                                       doInvert=True,
                                       doNormalize=True,
                                       streamingSleepOnWait=60,
                                       streamingBatchSize=0)
            protExtract.inputCoordinates.set(protPick2)
            protExtract.inputCoordinates.setExtended('outputCoordinates')
            _saveProtocol(protExtract, movies=False)

            prot2D = _newProtocol(ProtRelionClassify2D,
                                  objLabel='relion 2d - TEMPLATE',
                                  numberOfClasses=100,
                                  doGpu=True,
                                  extraParams="--maxsig 10",
                                  numberOfMpi=5,
                                  numberOfThreads=2)
            prot2D.inputParticles.set(protExtract)
            prot2D.inputParticles.setExtended('outputParticles')
            _saveProtocol(prot2D, movies=False)

            from pyworkflow.em import ProtMonitor2dStreamer

            protStreamer = _newProtocol(ProtMonitor2dStreamer,
                                        objLabel='scipion - 2d streamer',
                                        batchSize=20000)

            protStreamer.inputParticles.set(protExtract)
            protStreamer.inputParticles.setExtended('outputParticles')
            protStreamer.input2dProtocol.set(prot2D)
            _saveProtocol(protStreamer, movies=False)
