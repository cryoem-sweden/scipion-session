
import os
import datetime as dt
import json
import re
import sys
import codecs

import pyworkflow.em as em
import pyworkflow.utils as pwutils
from pyworkflow.manager import Manager

from config import *
from base import Person
from order import loadOrders, loadAccountsFromJson, loadActiveBags
from reservation import loadReservations
from session import SessionManager, Session
from user import loadUsersFromJsonFile
from datasource.portal import PortalManager

PROJ_NATIONAL = 0
PROJ_INTERNAL = 1
PROJ_FACILITY = 2


class Data:
    def __init__(self, **kwargs):
        self.dataFolder = kwargs['dataFolder']
        self.microscope = kwargs.get('microscope', None)
        self.now = dt.datetime.now()
        self.error = ''

        if 'date' in kwargs:
            self.date = kwargs['date']
            week = dt.timedelta(days=7)
            # Retrieve reservations from one week before to one week later
            # of the current date
            fromDate = self.date - week
            toDate = self.date + week
        elif 'fromDate' in kwargs:
            fromDate = kwargs['fromDate']
            toDate = kwargs['toDate']
            self.date = fromDate

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
        useLocal = int(os.environ.get('SESSION_WIZARD_LOCAL', 0))

        try:
            self._reservations = loadReservations(userJsonFn, reservationsFn,
                                                  fromDate, toDate,
                                                  fetchData=not useLocal)
        except Exception as ex:
            self._reservations = []  # work even without reservations

        print("Loaded reservations: ", len(self._reservations))

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
        self._reservation = None

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

            self._reservation = r
        else:
            print "No reservation found today for '%s'" % self.microscope

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

    def createSession(self, microscope, camera, projectType,
                      cem=None, pi=None, user=None, operator=None,
                      preprocessing=None):
        # Update now variable
        self.now = dt.datetime.now()

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


        if pi:
            session.pi = pi

        if user:
            session.user = user

        if operator:
            session.operator = operator

        session.printAll()

        self._createFolder(session.getPath())
        self._createSessionReadme(session)
        if preprocessing == 'Scipion':
            session.setScipionProjectName('%s_scipion_%s'
                                          % (session.getId(),
                                             self.getNowStr()))
            self._createSessionScipionProject(session)
        self.storeSession(session)

        return session

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
            r = self._reservation

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

    def storeSession(self, session):
        self.sMan.storeSession(session)

    def getSessions(self):
        return self.sMan.getSessions()

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

        useMC2 = True
        useMC = False
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
                                 useMotioncor2=useMC2,
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

    def getDataFile(self, filename):
        return os.path.join(self.dataFolder, filename)

    def getResourceFile(self, filename):
        return os.path.join(self.dataFolder, 'resources', filename)

    def getReservations(self):
        return self._reservations

    def getOrder(self, cemCode):
        return self._ordersDict.get(cemCode.lower(), None)

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

    def setProjectId(self, projId):
        self.projectId = projId
        if self.isNational():
            self.cemCode = projId

    def getProjectId(self):
        return self.projectId

    def _findNextProjectId(self):
        print "Finding next internal project id..."
        group = self.getProjectGroup()
        print "  group: ", group

        if not group in GROUP_DATA:
            self.error = ("ERROR!!! Invalid group '%s'. \n"
                          "Check that the user: %s has the correct "
                          "information in the BOOKING SYSTEM. "
                          % (group, self.user.getName()))
            return None

        folder = self.getDataFolder()
        print "  folder: ", folder

        if not os.path.exists(folder):
            self.error = ("ERROR!!! Folder '%s' does not exists. \n"
                          "This looks like a CONFIGURATION problem. \n"
                          "Contact the administrator. " % folder)
            return None

        last = 0
        groupRegex = re.compile("%s(\d{5})\Z" % group)
        for d in os.listdir(folder):
            if os.path.isdir(os.path.join(folder, d)):
                m = groupRegex.match(d)
                if m is None:
                    print "Warning: Invalid folder %s inside %s" % (d, folder)
                else:
                    n = int(m.group(1))
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

    def getActiveBags(self):
        return loadActiveBags(self.pMan)

    def getAccountsFromPortal(self):
        return loadAccountsFromJson(self.pMan.fetchAccountsJson(),
                                    isPi=False, university=None)