
import os
import datetime as dt
import json
import re
import sys
import codecs
from collections import OrderedDict

import pwem
import pyworkflow.utils as pwutils
from pyworkflow.project import Manager

from config import *
from model.base import Person
from model.session import Session, printSessions, SessionManager

PROJ_NATIONAL = 0
PROJ_INTERNAL = 1
PROJ_FACILITY = 2


class Data:
    def __init__(self, **kwargs):
        self.dataFolder = kwargs['dataFolder']
        self.microscope = kwargs.get('microscope', None)
        self.now = dt.datetime.now()
        self.error = ''

        self.fromDate = kwargs.get('fromDate', None)

        if self.fromDate is not None:
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

        print("Using day: ", self.date)

        self.sMan = SessionManager(self.getDataFile(SESSIONS_FILE))
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

        return self.findReservations(_active if status == 'active' else _starts)

    def findReservations(self, conditionFunc):
        """ Find reservations that satisfies the conditionFunc.
        The corresponding users will be set.
        """
        reservations = []

        for r in self._reservations:
            if conditionFunc(r):
                reservations.append(r)

        return reservations

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
            group = 'dbb'

        session = self.sMan.createSession(group)
        session.setMicroscopeDict(microscope=microscope, camera=camera)

        # Take only the first 3 character for the data folder
        session.preprocessing = preprocessing
        if preprocessing is not None:
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
        microscope = session.getMicroscope()
        camera = session.getCamera()
        path = session.getPath()

        manager = Manager()
        project = manager.createProject(session.getScipionProjectName(),
                                        location=path)

        # A custom workflow can be selected and then we will not modify it
        if 'workflow' in session.preprocessing:
            jsonFile = session.preprocessing['workflow']
            project.loadProtocols(jsonFile)
            return

        # If not, then we will customize the generic workflow

        jsonFile = getDataFile('workflows/scipion3_generic_workflow.json')
        project.loadProtocols(jsonFile)
        runsGraph = project.getRunsGraph(refresh=True)

        # Create a dict with class names and nodes for easier access
        nodeNames = {}
        for n in runsGraph.getNodes():
            p = n.run
            if p is not None:
                nodeNames[p.getClassName()] = n

        nodeImport = nodeNames['ProtImportMovies']
        nodeCompress = nodeNames['ProtRelionCompressMovies']
        nodeRelionMc = nodeNames['ProtRelionMotioncor']
        nodeMc = nodeNames['ProtMotionCorr']
        nodeCtffind = nodeNames['CistemProtCTFFind']
        nodeGctf = nodeNames['ProtGctf']

        # Update import parameters
        protImport = nodeImport.run
        protImport.setAttributesFromDict({
            'filesPath': path,
            'filesPattern': CAMERA_SETTINGS[camera][PATTERN]
        }, setBasic=False)
        project.saveProtocol(protImport)

        def _moveChilds(parent, newParent, inputName, outputName):
            for c in parent.getChilds():
                prot = c.run
                inputObj = getattr(prot, inputName)
                inputObj.set(newParent.run)
                inputObj.setExtended(outputName)
                project.saveProtocol(prot)

        # There is no need to compress if we are not using the
        # falcon3, let's remove that step from the workflow
        # and update the input for the dependent steps
        if camera != FALCON3:
            _moveChilds(nodeCompress, nodeImport,
                        'inputMovies', 'outputMovies')
            project.deleteProtocol(nodeCompress.run)

        opts = session.preprocessing['options']
        if opts['Motion correction'] == 'motioncor2':
            _moveChilds(nodeRelionMc, nodeMc,
                        'inputMicrographs', 'outputMicrographsDoseWeighted')
            protCtffind = nodeCtffind.run
            protCtffind.usePowerSpectra.set(False)
            project.saveProtocol(protCtffind)

        if opts['CTF estimation'] == 'gctf':
            _moveChilds(nodeCtffind, nodeGctf,
                        "ctfRelations", "outputCTF")

