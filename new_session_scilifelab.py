#!/usr/bin/env python
# **************************************************************************
# *
# * Authors:     J.M. De la Rosa Trevin (delarosatrevin@scilifelab)
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************

import os
import sys
import re
import Tkinter as tk
import tkFileDialog
import tkMessageBox
import ttk
import tkFont
from collections import OrderedDict
from ConfigParser import ConfigParser

import pyworkflow as pw
import pyworkflow.utils as pwutils
from pyworkflow.manager import Manager
from pyworkflow.gui import Message, Icon
from pyworkflow.config import ProjectSettings
import pyworkflow.em as em
import pyworkflow.gui as pwgui
from pyworkflow.gui.project.base import ProjectBaseWindow
from pyworkflow.gui.widgets import HotButton, Button
from pyworkflow.gui import Window, Message, Color

from model.users import loadUsers


VIEW_WIZARD = 'wizardview'

# Protocol's contants
MOTIONCORR = "MOTIONCORR"
MOTIONCOR2 = "MOTIONCOR2"
OPTICAL_FLOW = "OPTICAL_FLOW"
SUMMOVIE = "SUMMOVIE"
CTFFIND4 = "CTFFIND4"
GCTF = "GCTF"
EMAIL_NOTIFICATION = "EMAIL_NOTIFICATION"
HTML_REPORT = "HTML_REPORT"
GRIDS = "GRIDS"
CS = "CS"
MAG = "MAG"

# Some related environment variables
DATA_FOLDER = 'DATA_FOLDER'
USER_NAME = 'USER_NAME'
SAMPLE_NAME = 'SAMPLE_NAME'
PROJECT_NAME = 'PROJECT_NAME'
PROJECT_TYPE = 'PROJECT_TYPE'

SCIPION_PROJECT = 'SCIPION_PROJECT'
FRAMES_RANGE = 'FRAMES_RANGE'
MICROSCOPE = 'MICROSCOPE'
DATA_BACKUP = 'DATA_BACKUP'
PATTERN = 'PATTERN'
PUBLISH = 'PUBLISH'
SMTP_SERVER = 'SMTP_SERVER'
SMTP_FROM = 'SMTP_FROM'
SMTP_TO = 'SMTP_TO'

PROTOCOLS = "Protocols"
MONITORS = "Monitors"
MICROSCOPE = "Microscope"
MESSAGE = 'Message'

# Define some string constants
LABELS = {
    DATA_FOLDER: "Data folder",
    USER_NAME: "User name",
    SAMPLE_NAME: "Sample name",
    DATA_BACKUP: 'Data Backup Dir',
    PROJECT_NAME: "Project ID",
    PROJECT_TYPE: "Project Type",
    SCIPION_PROJECT: "Scipion project",
    FRAMES_RANGE: "Frames range",

    # Protocol's contants
    MOTIONCORR: "MotionCorr",
    MOTIONCOR2: "Use MotionCor2",
    OPTICAL_FLOW: "Optical Flow",
    SUMMOVIE: "Summovie (dose compensation)",
    CTFFIND4: "Ctffind4",
    GCTF: "GCtf",
    EMAIL_NOTIFICATION: "Email notification",
    HTML_REPORT: "HTML Report"
}

USER_GROUPS = ['cem', 'dbb', 'fac', 'int']
# Project ID should start by one of the previous groups
# followed by 5 digits code
PROJECT_REGEX = re.compile("(%s)(\d{5})$" % ('|'.join(USER_GROUPS)))


class Data():
    STAFF = ['marta.carroni@scilifelab.se',
             'julian.conrad@scilifelab.se']

    PROJECT_TYPES = ['National Facility Project',
                     'Internal Project']

    def __init__(self):
        self._users = loadUsers()
        self._usersDict = {}
        for u in self._users:
            self._usersDict[u.email.get()] = u
            u.isStaff = self._isUserStaff(u)
            u.group = self._getUserGroup(u)

        # Keep a configuration of user, project-type and project
        self.user = None
        self.projectType = None
        self.projectId = None
        self.group = None

    def _isUserStaff(self, user):
        return user.email.get() in self.STAFF

    def _getUserGroup(self, user):
        email = user.email.get()

        if not self._isUserStaff(user):
            if email.endswith('scilifelab.se'):
                return 'sll'

            if email.endswith('dbb.su.se'):
                return 'dbb'

        return 'fac'

    def getUserStringList(self):
        usList = []

        def _getStr(u):
            return "%s  -  %s" % (u.name.get(), u.email.get())

        # Add stuff personnel first
        for email in self.STAFF:
            usList.append(_getStr(self._usersDict[email]))
        # Add other users
        for u in self._users:
            if u.email.get() not in self.STAFF:
                usList.append(_getStr(u))

        return usList

    def getUserFromStr(self, userStr):
        name, email = userStr.split('-')
        return self._usersDict[email.strip()]

    def selectUser(self, user):
        self.user = user
        self.projectType = None if user.isStaff else self.PROJECT_TYPES[1]

    def selectProjectType(self, projType):
        self.projectType = projType
        if not self.user.isStaff:
            raise Exception("Project type only can be selected for "
                            "STAFF users.")
        self.group = 'cem' if self.isNational() else self.user.group

    def isNational(self):
        return self.projectType == self.PROJECT_TYPES[0]

    def getDataFolder(self):
        return '/data/staging/%s/' % self.group

    def getProjectId(self):
        if self.isNational():
            return 'cem00004' # grab this from the portalen
        else:
            # Grab this from the log of sessions
            return '%s%05d' % (self.group, 3)


class BoxWizardWindow(ProjectBaseWindow):
    """ Windows to manage all projects. """

    def __init__(self, config, **kwargs):
        try:
            title = '%s (%s on %s)' % (Message.LABEL_PROJECTS,
                                       pwutils.getLocalUserName(),
                                       pwutils.getLocalHostName())
        except Exception:
            title = Message.LABEL_PROJECTS

        settings = ProjectSettings()
        self.generalCfg = settings.getConfig()

        self.config = config
        self.data = Data()
        ProjectBaseWindow.__init__(self, title, minsize=(400, 550), **kwargs)
        self.viewFuncs = {VIEW_WIZARD: BoxWizardView}
        self.manager = Manager()
        self.switchView(VIEW_WIZARD)

    def createHeaderFrame(self, parent):

        """ Create the Header frame at the top of the windows.
        It has (from left to right):
            - Main application Logo
            - Project Name
            - View selection combobox
        """
        # Create the Project Name label
        self.projNameFont = tkFont.Font(size=-28, family='helvetica')
        self.projNameFontBold = tkFont.Font(size=-28, family='helvetica',
                                            weight='bold')

        header = tk.Frame(parent, bg='black')
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=1)
        #header.columnconfigure(2, weight=1)
        # Create the SCIPION logo label
        cwd = os.getcwd()
        logoPath = os.path.join(cwd, 'resources', 'scilifelab-logo.png')
        logoImg = self.getImage(logoPath, maxheight=50)

        # SciLifeLab logo in the header
        headerImg = tk.Label(header, image=logoImg,
                             borderwidth=0, bg='black')
        headerImg.grid(row=0, column=0, sticky='nw', padx=(10, 0), pady=10)

        # Swedish National Cryo-EM Facility
        headerText = tk.Label(header, borderwidth=0, bg='black',
                             text='Swedish National Cryo-EM Facility',
                             fg='white',
                             font=self.projNameFontBold)
        headerText.grid(row=0, column=1, sticky='se',
                        padx=(5, 15), pady=(20, 5))

        return header


class BoxWizardView(tk.Frame):
    def __init__(self, parent, windows, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        self.windows = windows
        self.manager = windows.manager
        self.data = windows.data
        self.root = windows.root
        self.vars = {}
        self.checkvars = []
        self.microscope = None
        # Regular expression to validate username and sample name
        self.re = re.compile('\A[a-zA-Z][a-zA-Z0-9_-]+\Z')

        # tkFont.Font(size=12, family='verdana', weight='bold')
        bigSize = pwgui.cfgFontSize + 2
        smallSize = pwgui.cfgFontSize - 2
        fontName = pwgui.cfgFontName

        self.bigFont = tkFont.Font(size=bigSize, family=fontName)
        self.bigFontBold = tkFont.Font(size=bigSize, family=fontName,
                                       weight='bold')

        self.projDateFont = tkFont.Font(size=smallSize, family=fontName)
        self.projDelFont = tkFont.Font(size=smallSize, family=fontName,
                                       weight='bold')
        self.manager = Manager()



        # Header section
        headerFrame = tk.Frame(self, bg='white')
        headerFrame.grid(row=0, column=0, sticky='new')
        headerText = "Create New Session"

        headerText += "  %s" % pwutils.prettyTime(dateFormat='%Y-%m-%d')

        label = tk.Label(headerFrame, text=headerText,
                         font=self.bigFontBold,
                         borderwidth=0, anchor='nw', bg='white',
                         fg=pwgui.Color.DARK_GREY_COLOR)
        label.grid(row=0, column=0, sticky='nw', padx=(20, 5), pady=10)

        # Body section
        bodyFrame = tk.Frame(self, bg='white')
        bodyFrame.grid(row=1, column=0, sticky='news')
        self._fillContent(bodyFrame)

        # Add the create project button
        btnFrame = tk.Frame(self, bg='white')
        btn = HotButton(btnFrame, text="Create New Session",
                        font=self.bigFontBold,
                        command=self._onAction)
        btn.grid(row=0, column=1, sticky='ne', padx=10, pady=10)

        # Add the Import project button
        btn = Button(btnFrame, Message.LABEL_BUTTON_CANCEL,
                     Icon.ACTION_CLOSE,
                     font=self.bigFontBold,
                     command=self.windows.close)
        btn.grid(row=0, column=0, sticky='ne', padx=10, pady=10)

        btnFrame.grid(row=2, column=0, sticky='sew')
        btnFrame.columnconfigure(0, weight=1)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

    def _storeVarWidgets(self, key, var, widget):
        self.vars[key] = (var, widget)

    def _getVar(self, key):
        v, _ = self.vars[key]
        return v

    def _getVarValue(self, key):
        return self._getVar(key).get()

    def _setVarValue(self, key, value):
        return self._getVar(key).set(value)

    def _showWidgets(self, key, value):
        _, widget = self.vars[key]
        print "_showWidget: key=%s, value=%s" % (key, value)
        if value:
            widget.grid(sticky='news')
        else:
            widget.grid_forget()

    def _fillContent(self, content):
        tab = ttk.Notebook(content)  # , style='W.TNotebook')
        tab.grid(row=0, column=0, sticky='news', padx=10, pady=10)

        content.rowconfigure(0, weight=1)
        content.columnconfigure(0, weight=1)

        self._lastRow = 0
        self._lastFrame = None

        def _createTabFrame(text):
            lf = tk.LabelFrame(tab, text=text, font=self.bigFontBold)
            tab.add(lf, text=text, sticky='news', padding=10)
            self._lastFrame = lf
            return lf

        def _newRow():
            v = self._lastRow
            self._lastRow += 1
            return v

        def _getContainerFrame(**kwargs):
            """ Request for a new row and create two frames, one to hold the
            row position and another one that can be show/hidden.
            """
            lf = self._lastFrame
            r = _newRow()
            parent = tk.Frame(lf)
            parent.grid(row=r, sticky='news')
            parent.columnconfigure(0, weight=1)
            parent.rowconfigure(0, weight=1)

            frame = tk.Frame(parent)
            frame.grid(row=0, sticky='news')
            frame.columnconfigure(0, minsize=180)
            frame.columnconfigure(1, weight=1)

            if not kwargs.get('visible', True):
                frame.grid_forget()

            return frame

        def _addPair(key, widget='entry', **kwargs):
            frame = _getContainerFrame(**kwargs)

            t = LABELS.get(key, key)
            label = tk.Label(frame, text=t, font=self.bigFont)
            label.grid(row=0, column=0, padx=(10, 5), pady=2, sticky='ne')

            if not widget:
                return

            var = tk.StringVar()

            if widget == 'entry':
                widget = tk.Entry(frame, width=30, font=self.bigFont,
                                 textvariable=var)
                traceCallback = kwargs.get('traceCallback', None)
                mouseBind = kwargs.get('mouseBind', None)

                if traceCallback:
                    if mouseBind: #call callback on click
                        widget.bind("<Button-1>", traceCallback, "eee")
                    else:#call callback on type
                        var.trace('w', traceCallback)
            elif widget == 'label':
                widget = tk.Label(frame, font=self.bigFont, textvariable=var)

            widget.grid(row=0, column=1, sticky='nw', padx=(5, 10), pady=2)

            self._storeVarWidgets(key, var, frame)

        def _addCheckPair(key, col=1):
            lf = self._lastFrame
            r = _newRow() if col == 1 else self._lastRow
            t = LABELS.get(key, key)
            var = tk.IntVar()

            cb = tk.Checkbutton(lf, text=t, font=self.bigFont, variable=var)
            self.checkvars.append(key)
            cb.grid(row=r, column=col, padx=5, sticky='nw')
            self._storeVarWidgets(key, var, cb)

        def _addComboPair(key, **kwargs):
            t = LABELS.get(key, key)
            frame = _getContainerFrame(**kwargs)
            label = tk.Label(frame, text=t, font=self.bigFont)
            label.grid(row=0, column=0, padx=(10, 5), pady=2, sticky='ne')

            var = tk.StringVar()
            combo = ttk.Combobox(frame, textvariable=var, state='readonly',
                                 width=40)
            values = kwargs.get('values', None)
            combo['values'] = values or self._getConfig().keys()

            traceCallback = kwargs.get('traceCallback', None)

            if traceCallback:
                combo.bind('<<ComboboxSelected>>', traceCallback)

            combo.grid(row=0, column=1, sticky='nw', padx=(5, 10), pady=(10, 2))
            self._storeVarWidgets(key, var, frame)


            return combo

        lfProject = _createTabFrame(' Project ')
        lfProject.columnconfigure(0, weight=1)

        lfProject.columnconfigure(1, weight=1)

        self.userCombo = _addComboPair(USER_NAME,
                                       values=self.data.getUserStringList(),
                                       traceCallback=self._onUserChanged)
        self.projectCombo = _addComboPair(PROJECT_TYPE,
                                          values=Data.PROJECT_TYPES,
                                          traceCallback=self._onProjectTypeChanged,
                                          visible=False)

        _addPair(PROJECT_NAME, widget='entry',
                 traceCallback=self._onInputChange,
                 visible=False)
        _addPair(DATA_FOLDER, widget='label')
        _addPair(SCIPION_PROJECT, widget='label')
        _addPair(MESSAGE, widget='label')

        lfSettinglabelFrame = _createTabFrame(' Settings ')
        self.micCombo = _addComboPair(MICROSCOPE,
                                      traceCallback=self._onMicroscopeChanged)

        labelFrame2 = _createTabFrame(' Pre-processing ')
        labelFrame2.columnconfigure(0, minsize=120)
        _addPair(FRAMES_RANGE)
        _addPair(PROTOCOLS, widget=False)
        _addCheckPair(MOTIONCORR)
        _addCheckPair(MOTIONCOR2, col=2)
        _addCheckPair(OPTICAL_FLOW)
        _addCheckPair(SUMMOVIE)
        _addCheckPair(CTFFIND4)
        _addCheckPair(GCTF, col=2)
        _addPair("Monitors", widget=False)
        _addCheckPair(EMAIL_NOTIFICATION)
        _addCheckPair(HTML_REPORT, col=2)

        content.columnconfigure(0, weight=1)

        self._onInputChange()

    def _getConfValue(self, key, default=''):
        return self.windows.config[self.microscope].get(key, default)

    def _getConfig(self):
        return self.windows.config


    def _onAction(self, e=None):
        errors = []
        doBackup = True
        # Check the Data folder exists
        dataFolder = self._getDataFolder()
        projName = self._getProjectName()
        projPath = dataFolder
        scipionProj = self._getScipionProject()
        scipionProjPath = os.path.join(projPath, scipionProj)
        # Do more checks only if there are not previous errors
        if not self._validProjectName():
            errors.append("Project ID should start with the group name"
                          "followed by five digits."
                          "Possible groups are: %s"
                          "Examples: \n   int00012\n   dbb00028\n   fac00003")
        if not errors:
            if os.path.exists(scipionProjPath):
                errors.append("Scipion Project path '%s' already exists."
                              % scipionProjPath)

        if not errors:
            if not (self._getVarValue(MOTIONCORR) or self._getVarValue(MOTIONCOR2)
                    or self._getVarValue(OPTICAL_FLOW)):
                errors.append("You should use at least one alignment method."
                              "(%s or %s)" % (MOTIONCORR, OPTICAL_FLOW))

        if errors:
            errors.insert(0, "*Errors*:")
            self.windows.showError("\n  - ".join(errors))
        else:
            self._createDataFolder(projPath, scipionProjPath)
            self._createScipionProject(projName, projPath, scipionProjPath)
            self.windows.close()

    def _createDataFolder(self, projPath, scipionProjPath):
        def _createPath(p):
            # Create the project path
            sys.stdout.write("Creating path '%s' ... " % p)
            pwutils.makePath(p)
            sys.stdout.write("DONE\n")

        _createPath(projPath)
        _createPath(scipionProjPath)

    def _createScipionProject(self, projName, projPath, scipionProjPath):
        manager = Manager()
        project = manager.createProject(projName, location=scipionProjPath)
        self.lastProt = None
        pattern = self._getConfValue(PATTERN)

        smtpServer = self._getConfValue(SMTP_SERVER, '')
        smtpFrom = self._getConfValue(SMTP_FROM, '')
        smtpTo = self._getConfValue(SMTP_TO, '')
        doMail = self._getVarValue(EMAIL_NOTIFICATION)
        doPublish = self._getVarValue(HTML_REPORT)

        protImport = project.newProtocol(em.ProtImportMovies,
                                         objLabel='Import movies',
                                         filesPath=projPath,
                                         filesPattern=pattern,
                                         sphericalAberration=self._getConfValue(CS),
                                         dataStreaming=True)

        # Should I publish html report?       
        if doPublish == 1:
            publish = self._getConfValue('HTML_PUBLISH')
            print("\n\nReport available at URL: %s/%s\n\n"
                  %('http://scipion.cnb.csic.es/scipionbox',projName))
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

        _saveProtocol(protImport, movies=False)

        useMC2 = self._getVarValue(MOTIONCOR2)
        useMC = self._getVarValue(MOTIONCORR) or useMC2
        useOF = self._getVarValue(OPTICAL_FLOW)
        useSM = self._getVarValue(SUMMOVIE)
        useCTF = self._getVarValue(CTFFIND4)
        useGCTF = self._getVarValue(GCTF)

        kwargs = {}
        frames = self._getVarValue(FRAMES_RANGE).split()
        if frames:
            kwargs['alignFrame0'] = kwargs['sumFrame0'] = frames[0]
            kwargs['alignFrameN'] = kwargs['sumFrameN'] = frames[1]

        if useMC:
            # Create motioncorr
            from pyworkflow.em.packages.motioncorr import ProtMotionCorr
            protMC = project.newProtocol(ProtMotionCorr,
                                         objLabel='Motioncorr',
                                         useMotioncor2=useMC2,
                                         **kwargs)
            _saveProtocol(protMC)

        if useOF:
            # Create Optical Flow protocol
            from pyworkflow.em.packages.xmipp3 import XmippProtOFAlignment

            protOF = project.newProtocol(XmippProtOFAlignment,
                                         objLabel='Optical Flow',
                                         doSaveMovie=useSM,
                                         **kwargs)
            _saveProtocol(protOF)

        if useSM:
            # If OF write the movie, then we need to reset frames count
            if frames and useOF:
                kwargs['alignFrame0'] = kwargs['sumFrame0'] = 1
                kwargs['alignFrameN'] = kwargs['sumFrameN'] = 0

            from pyworkflow.em.packages.grigoriefflab import ProtSummovie
            protSM = project.newProtocol(ProtSummovie,
                                         objLabel='Summovie',
                                         cleanInputMovies=useOF,
                                         numberOfThreads=1,
                                         **kwargs)
            _saveProtocol(protSM)

        lastBeforeCTF = self.lastProt

        if useCTF:
            from pyworkflow.em.packages.grigoriefflab import ProtCTFFind
            protCTF = project.newProtocol(ProtCTFFind,
                                          objLabel='Ctffind',
                                          numberOfThreads=1)
            protCTF.inputMicrographs.set(lastBeforeCTF)
            protCTF.inputMicrographs.setExtended('outputMicrographs')
            _saveProtocol(protCTF, movies=False)

        if useGCTF:
            from pyworkflow.em.packages.gctf import ProtGctf
            protGCTF = project.newProtocol(ProtGctf,
                                           objLabel='Gctf')
            protGCTF.inputMicrographs.set(lastBeforeCTF)
            protGCTF.inputMicrographs.setExtended('outputMicrographs')
            _saveProtocol(protGCTF, movies=False)

        project.saveProtocol(protMonitor)

        os.system('%s project %s &' % (pw.getScipionScript(), projName))

        self.windows.close()

    def _replaceVars(self, value):
        newValue = value
        for v in [USER_NAME, SAMPLE_NAME]:
            newValue = newValue.replace('${%s}' % v, self._getVarValue(v))

        return newValue

    def _getProjectName(self):
        return self._getVarValue(PROJECT_NAME)

    def _validProjectName(self):
        return PROJECT_REGEX.match(self._getProjectName())

    def _isInputReady(self):
        return self.microscope is not None and self._validProjectName()

    def _getDataFolder(self):
        if not self._isInputReady():
            return ''
        dataFolder = self._getConfValue(DATA_FOLDER)
        projName = self._getProjectName()
        groups = PROJECT_REGEX.match(projName).groups()

        dataFolder = os.path.join(dataFolder, groups[0], projName)
        return dataFolder

    def _getScipionProject(self):
        if not self._isInputReady():
            return ''
        scipionProj = self._getConfValue(SCIPION_PROJECT)
        return scipionProj.replace('${PROJECT_NAME}', self._getProjectName())

    def _checkInput(self, varKey):
        value = self._getVarValue(varKey)

    def fileDialog(self, * args):
        """callback that display a directory dialog window"""
        try:
             initialdir = self._getConfValue(DATA_BACKUP, '')
        except:
            tkMessageBox.showerror("Error","Please select Microscope first")
            return
        backupFolder = tkFileDialog.askdirectory(parent=self.root,
                                                 initialdir=initialdir,
                                                 title='Choose Backup directory')
        self._setVarValue(DATA_BACKUP, backupFolder)

    def _onInputChange(self, *args):
        pass

    def _updateData(self):
        self._setVarValue(DATA_FOLDER, self.data.getDataFolder())
        self._setVarValue(SCIPION_PROJECT, self._getScipionProject())

    def _onUserChanged(self, *args):
        username = self._getVarValue(USER_NAME)
        if not username:
            return

        user = self.data.getUserFromStr(username)
        self.data.selectUser(user)
        self._showWidgets(PROJECT_TYPE, user.isStaff)
        self._updateData()

    def _onProjectTypeChanged(self, *args):
        projectType = self._getVarValue(PROJECT_TYPE)
        if not projectType:
            return

        self.data.selectProjectType(projectType)
        isNational = self.data.isNational()
        self._showWidgets(PROJECT_NAME, not isNational)
        self._updateData()


    def _onMicroscopeChanged(self, *args):
        self.microscope = self._getVarValue(MICROSCOPE)
        self.micCombo.selection_clear()
        # Check/uncheck different options
        for key in self.checkvars:
            self._setVarValue(key, int(self._getConfValue(key, 0)))

        self._onInputChange()


def createDictFromConfig():
    """ Read the configuration from scipion/config/scipionbox.conf.
     A dictionary will be created where each key will be a section starting
     by MICROSCOPE:, all variables that are in the GLOBAL section will be
     inherited by default.
    """
    # Read from users' config file.
    confGlobalDict = OrderedDict()
    confDict = OrderedDict()

    cp = ConfigParser()
    cp.optionxform = str  # keep case (stackoverflow.com/questions/1611799)

    confFile = pw.getConfigPath("scipionbox.conf")

    print "Reading conf file: ", confFile
    cp.read(confFile)

    GLOBAL = "GLOBAL"
    MICROSCOPE = "MICROSCOPE:"

    if not GLOBAL in cp.sections():
        raise Exception("Missing section %s in %s" % (GLOBAL, confFile))
    else:
        for opt in cp.options(GLOBAL):
            confGlobalDict[opt] = cp.get(GLOBAL, opt)

    for section in cp.sections():
        if section != GLOBAL and section.startswith(MICROSCOPE):
            sectionDict = OrderedDict(confGlobalDict)
            for opt in cp.options(section):
                sectionDict[opt] = cp.get(section, opt)
            confDict[section.replace(MICROSCOPE, '')] = sectionDict

    return confDict


if __name__ == "__main__":
    confDict = createDictFromConfig()

    wizWindow = BoxWizardWindow(confDict)
    wizWindow.show()
