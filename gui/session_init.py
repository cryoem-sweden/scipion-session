# **************************************************************************
# *
# * Authors:     J.M. De la Rosa Trevin (delarosatrevin@scilifelab.se) [1]
# *
# * [1] SciLifeLab, Stockholm University
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
from collections import OrderedDict
import datetime as dt
import codecs
import Tkinter as tk
import ttk
import tkFont

import pyworkflow as pw
import pyworkflow.utils as pwutils
import pyworkflow.gui as pwgui
from pyworkflow.gui.project.base import ProjectBaseWindow
from pyworkflow.gui.widgets import HotButton, Button
from pyworkflow.manager import Manager
from pyworkflow.gui import Message, Icon
from pyworkflow.config import ProjectSettings
import pyworkflow.em as em

from chooser import OptionChooser

from config import *


class BoxWizardWindow(ProjectBaseWindow):
    """ Windows to manage all projects. """

    def __init__(self, **kwargs):
        try:
            title = '%s (%s on %s)' % ('Session Wizard',
                                       pwutils.getLocalUserName(),
                                       pwutils.getLocalHostName())
        except Exception:
            title = Message.LABEL_PROJECTS

        settings = ProjectSettings()
        self.generalCfg = settings.getConfig()

        self.data = kwargs.get('data')
        self.microscope = self.data.microscope

        ProjectBaseWindow.__init__(self, title, minsize=(800, 700), **kwargs)
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

        logoPath = self.data.getResourceFile('scilifelab-logo.png')
        logoImg = self.getImage(os.path.abspath(logoPath), maxheight=50)

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
        self.microscope = self.windows.microscope
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

        bigfont = tkFont.Font(family="Helvetica", size=12)
        #self.option_add("*TCombobox*Listbox*Font", bigfont)
        self.option_add("*Font", bigfont)
        self.manager = Manager()

        # Header section
        headerFrame = tk.Frame(self)
        headerFrame.grid(row=0, column=0, sticky='new')
        headerText = "Create New Session"

        headerText += "  %s" % pwutils.prettyTime(dateFormat='%Y-%m-%d')

        label = tk.Label(headerFrame, text=headerText,
                         font=self.bigFontBold,
                         borderwidth=0, anchor='nw', #bg='white',
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
        if not key in self.vars:
            return None

        return self._getVar(key).get()

    def _setVarValue(self, key, value):
        return self._getVar(key).set(value)

    def _showWidgets(self, key, value):
        _, widget = self.vars[key]
        if value:
            widget.grid(sticky='news')
        else:
            widget.grid_forget()

    def _fillContent(self, content):
        frame = tk.Frame(content, bg='white')
        frame.grid(row=0, column=0, sticky='news', padx=10, pady=15)
        frame.columnconfigure(0, minsize=200)
        self._lastRow = 0

        def __addLabeledWidget(text, widget=None, pady=5, bold=False):
            boldStr = 'bold' if bold else ''
            label = tk.Label(frame, text=text,
                             font="helvetica 12 %s" % boldStr, bg='white')
            label.grid(row=self._lastRow, column=0, sticky='ne', pady=pady)

            if widget is not None:
                widget.grid(row=self._lastRow, column=1, sticky='nw', pady=pady, padx=5)

            self._lastRow += 1

            return label

        def __createCombobox(options, readOnly=True, callback=None, width=38):
            var = tk.StringVar()
            s = ttk.Style()
            state = 'readonly' if readOnly else 'edit'
            combo = ttk.Combobox(frame, textvariable=var, state=state,
                                 width=width)
            combo['values'] = options
            combo.var = var

            if callback:
                combo.bind('<<ComboboxSelected>>', callback)

            return combo

        def _showCameraOptions(chooser):
            """ Show the correct camera options depending on the
            selected microscope. """
            i = chooser.getSelectedIndex()
            j = 1 - i  # old index, this works only for two values
            print("changed mic selection...", i, j)
            self._camChoosers[j].grid_forget()
            self._camChoosers[i].grid(row=self._camRow, column=1, sticky='nw',
                                      pady=5, padx=5)

        def _configCombo(combo, selection='', values=[]):
            combo.set(selection)
            combo['values'] = values

        def _getAccountList(filterFunc):
            """ Return a list of strings name -- email
            for all the accounts that meets the filterFunc criteria.
            """
            return ['%s %s -- %s' %
                    (a['first_name'], a['last_name'], a['email'])
                    for a in self._accounts if filterFunc(a)]

        def _getEmailFromCombo(combo):
            """ Return the account email assuming the format name -- email. """
            return combo.var.get().split('--')[1].strip()

        def _onChangeProjectType(chooser):
            piConfig = {}
            cemConfig = {'selection': 'None'}

            i = chooser.getSelectedIndex()
            # 0 is National, 1 is Internal, 2 Facility
            if i == 0:
                piConfig = {'selection': 'Select CEM code first'}
                cemConfig = {'selection': 'Select CEM',
                             'values': self._bagsDict.keys()}
            elif i == 1:
                # List of internal PIs of SU
                piFilter = lambda a: a['pi'] and a['university'] == 'SU'
                piConfig = {'selection': 'Select PI',
                            'values': _getAccountList(piFilter)}
            elif i == 2:
                piConfig['selection'] = 'None'
            else:
                raise Exception('Invalid option for project type %s' % i)

            _configCombo(self._piCombo, **piConfig)
            _configCombo(self._cemCombo, **cemConfig)
            _configCombo(self._userCombo)

        def _onSelectCEM(*args):
            #for name, email in piList:
            print "value: ", self._cemCombo.var.get()
            bag = self._bagsDict.get(self._cemCombo.var.get(), None)
            _configCombo(self._piCombo,
                         values=['%s -- %s' % tuple(pi) for pi in bag.piList])

        def _onSelectPI(*args):
            piEmail = _getEmailFromCombo(self._piCombo)
            print "value: ", piEmail
            userFilter = lambda a: a['invoice_ref'] == piEmail
            # bag = self._bagsDict.get(self._cemCombo.var.get(), None)
            _configCombo(self._userCombo,
                         values=_getAccountList(userFilter))

        EXTRA_PAD = 30

        f1 = OptionChooser(frame, bg='white', optionWidth=200)
        f1.onSelectionChanged(_showCameraOptions)
        f1.addOption('Krios 1', self.data.getResourceFile("titan_small.gif"))
        f1.addOption('Talos', self.data.getResourceFile("talos_small.gif"))
        __addLabeledWidget("Microscope", f1, bold=True)
        self._micOrder = {TITAN: 0, TALOS: 1}

        f2 = OptionChooser(frame, bg='white', optionWidth=200)
        #f2.onSelectionChanged(onSelection)
        f2.addOption('K2')
        f2.addOption('Falcon 3')
        self._camRow = self._lastRow
        __addLabeledWidget("Camera", f2)

        f2b = OptionChooser(frame, bg='white', optionWidth=200)
        #f2.onSelectionChanged(onSelection)
        f2b.addOption('Falcon 3')
        f2b.selectIndex(0)

        self._camChoosers = [f2, f2b]

        # --------- Load some data ---------------
        self._bagsDict = OrderedDict([(b.getId().upper(), b)
                                      for b in self.data.getActiveBags()])

        self._accounts = self.data.getAccountsFromPortal()

        # --------- Project block ----------------
        f3 = OptionChooser(frame, bg='white',
                           optionWidth=134)
        f3.onSelectionChanged(_onChangeProjectType)
        f3.addOption('National')
        f3.addOption('Internal')
        f3.addOption('Facility')
        __addLabeledWidget("Project", f3, pady=(EXTRA_PAD, 0), bold=True)

        self._cemCombo = __createCombobox([], callback=_onSelectCEM, width=11)
        __addLabeledWidget("CEM code", self._cemCombo)

        self._piCombo = __createCombobox([], callback=_onSelectPI)
        __addLabeledWidget("PI", self._piCombo)

        self._userCombo = __createCombobox([], readOnly=False)
        __addLabeledWidget("User", self._userCombo)

        __addLabeledWidget("Operator", __createCombobox(['Marta', 'Julian']))

        f4 = OptionChooser(frame, bg='white', optionWidth=200)
        f4.addOption('Scipion', self.data.getResourceFile("scipion_logo.gif"))
        f4.addOption('None', self.data.getResourceFile("none.gif"))

        # --------- Preprocessing block ----------------
        __addLabeledWidget("Session ID", f4, pady=(EXTRA_PAD, 0), bold=True)

        # --------- Preprocessing block ----------------
        __addLabeledWidget("Pre-processing", f4, pady=(EXTRA_PAD, 0), bold=True)

        # Select Krios, TESTING
        f1.selectIndex(self._micOrder[self.microscope])
        # Select Scipion as default for pre-processing
        f4.selectIndex(0)

    def _fillContentOLD(self, content):
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

        def _getContainerFrame(parent=None, **kwargs):
            """ Request for a new row and create two frames, one to hold the
            row position and another one that can be show/hidden.
            """
            if parent is None:
                lf = self._lastFrame
                r = _newRow()
                parent = tk.Frame(lf)
                parent.grid(row=r, sticky='news')
                parent.columnconfigure(0, weight=1)
                parent.rowconfigure(0, weight=1)

            frameCol = kwargs.get('frameCol', 0)
            frame = tk.Frame(parent)
            frame.grid(row=0, column=frameCol, sticky='news')
            frame.columnconfigure(0, minsize=180)
            frame.columnconfigure(1, weight=1)

            if not kwargs.get('visible', True):
                frame.grid_forget()

            return parent, frame

        def _addPair(key, widget='entry', **kwargs):
            _, frame = _getContainerFrame(**kwargs)

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

        def _addCheckPair(*keys, **kwargs):
            _, frame = _getContainerFrame(**kwargs)

            label = kwargs.get('label', None)

            if label is not None:
                label = tk.Label(frame, text=label, font=self.bigFont)
                label.grid(row=0, column=0, padx=(10, 5), pady=2, sticky='ne')

            for i, key in enumerate(keys):
                checkFrame = tk.Frame(frame)
                c = i + 1
                checkFrame.grid(row=0, column=c, sticky='news')
                frame.columnconfigure(c, weight=1)
                frame.columnconfigure(c, minsize=200)
                t = LABELS.get(key, key)
                var = tk.IntVar()

                cb = tk.Checkbutton(checkFrame, text=t, font=self.bigFont,
                                    variable=var)

                # This is used later to get values for preprocessing
                if kwargs.get('isCheckVar', True):
                    self.checkvars.append(key)

                traceCallback = kwargs.get('traceCallback', None)
                if traceCallback:
                    var.trace('w', traceCallback)

                cb.grid(row=0, column=0, padx=5, sticky='nw')

                self._storeVarWidgets(key, var, frame)

        def _addComboPair(key, **kwargs):
            t = LABELS.get(key, key)
            _, frame = _getContainerFrame(**kwargs)
            label = tk.Label(frame, text=t, font=self.bigFont)
            label.grid(row=0, column=0, padx=(10, 5), pady=2, sticky='ne')

            var = tk.StringVar()
            combo = ttk.Combobox(frame, textvariable=var, state='readonly',
                                 width=40)
            combo['values'] = kwargs.get('values')
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
                                          values=PROJECT_TYPES,
                                          traceCallback=self._onProjectTypeChanged,
                                          visible=False)

        self.projIdCombo = _addComboPair(PROJECT_ID, widget='entry', values=[],
                                         traceCallback=self._onProjectChanged,
                                         visible=False)
        _addPair(PROJECT_FOLDER, widget='label', visible=False)

        _createTabFrame(' Settings ')
        self.micCombo = _addComboPair(MICROSCOPE, values=MICROSCOPES,
                                      traceCallback=self._onMicroscopeChanged)
        self.camCombo = _addComboPair(CAMERA, values=[])


        _createTabFrame(' Pre-processing ')
        _addCheckPair(SCIPION_PREPROCESSING, label='',
                      traceCallback=self._showProcessingOptions)
        _addPair(SCIPION_PROJECT, widget='label')
        _addPair(FRAMES_RANGE)
        _addCheckPair(MOTIONCORR, MOTIONCOR2, label=MOTION_CORRECTION)
        _addCheckPair(CTFFIND4, GCTF, label=CTF_ESTIMATION)
        _addCheckPair(EMAIL_NOTIFICATION, HTML_REPORT, label="Monitors")

        content.columnconfigure(0, weight=1)

        # Select the initial user if one by default
        user = self.data.getSelectedUser()
        if user is not None:
            self._setVarValue(USER_NAME, self.data.getUserString(user))
            projType = self.data.getProjectType()
            if projType is not None:
                self._setVarValue(PROJECT_TYPE, projType)
            self._updateUserInfo(self.data.getSelectedUser())

        # Select initial value for the microscope
        self._setVarValue(MICROSCOPE, self.microscope)
        self._onMicroscopeChanged()

        self._setProcessingOptions()

    def _getConfValue(self, key, default=''):
        return DEFAULTS.get(key, default)

    def _onAction(self, e=None):
        errors = []
        if self.data.error:
            errors.append(self.data.error)

        if not errors:
            # Check the Data folder exists
            projPath = self.data.getProjectFolder()
            scipionProjPath = self.data.getScipionProjectFolder()
            projName = self.data.getScipionProject()

            if (self.data.isNational() and
                self.data.getOrderDetails() is None):
                errors.append("Error loading Order %s, check that it is correct. "
                              % self.data.getProjectId())

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
            self.data.storeSession(projPath, projName)
            self._createDataFolder(projPath, scipionProjPath)
            self._createScipionProject(projName, projPath, projPath)
            self.windows.close()

    def _createDataFolder(self, projPath, scipionProjPath):
        def _createPath(p):
            if os.path.exists(p):
                sys.stdout.write("Path '%s' exists, not need to create it.\n" % p)
                return
            # Create the project path
            sys.stdout.write("Creating path '%s' ... " % p)
            pwutils.makePath(p)
            sys.stdout.write("DONE\n")

        _createPath(projPath)
        now = dt.datetime.now()
        dateTuple = (now.year, now.month, now.day)
        readmeFn = os.path.join(projPath, 'README_%04d%02d%02d.txt' % dateTuple)
        readmeFile = codecs.open(readmeFn, "w", "utf-8")
        u = self.data.getSelectedUser()
        r = self.data.getSelectedReservation()
        desc = "Not found" if r is None else r.title

        readmeFile.write("name: %s\n" % u.getFullName())
        readmeFile.write("email: %s\n" % u.getEmail())
        readmeFile.write("description: %s\n" % desc)
        readmeFile.write("date: %d-%02d-%02d\n" % dateTuple)

        readmeFile.close()

        _createPath(scipionProjPath)

    def _createScipionProject(self, projName, projPath, scipionProjPath):
        manager = Manager()
        projId = self.data.getProjectId()
        project = manager.createProject(projName, location=scipionProjPath)
        self.lastProt = None


        smtpServer = self._getConfValue(SMTP_SERVER, '')
        smtpFrom = self._getConfValue(SMTP_FROM, '')
        smtpTo = self._getConfValue(SMTP_TO, '')
        doMail = self._getVarValue(EMAIL_NOTIFICATION)
        doPublish = self._getVarValue(HTML_REPORT)

        microscope = self._getVarValue(MICROSCOPE)
        camera = self._getVarValue(CAMERA)

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
        filesPath = projPath

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
            # If OF write the movie, then we need to reset frames count
            if frames and useOF:
                kwargs['alignFrame0'] = kwargs['sumFrame0'] = 1
                kwargs['alignFrameN'] = kwargs['sumFrameN'] = 0

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

        os.system('%s project %s &' % (pw.getScipionScript(), projName))

        self.windows.close()

    def _replaceVars(self, value):
        newValue = value
        for v in [USER_NAME, SAMPLE_NAME]:
            newValue = newValue.replace('${%s}' % v, self._getVarValue(v))

        return newValue

    def _isInputReady(self):
        return self.microscope is not None and self._validProjectName()

    def _checkInput(self, varKey):
        value = self._getVarValue(varKey)

    def _onInputChange(self, *args):
        pass

    def _setProcessingOptions(self):
        # Check/uncheck different options
        for key in self.checkvars:
            self._setVarValue(key, 1 if self._getConfValue(key) else 0)

        self._showProcessingOptions()

    def _showProcessingOptions(self, *args):
        prep = self._getVarValue(SCIPION_PREPROCESSING)
        for key in self.checkvars:
            if key != SCIPION_PREPROCESSING:
                self._showWidgets(key, prep)
        self._showWidgets(FRAMES_RANGE, prep)

    def _updateData(self):
        print "DEBUG: _updateData: projectType: ", self.data.getProjectType()
        if self.data.getProjectType() is None:
            self._setVarValue(PROJECT_TYPE, '')
            self._showWidgets(PROJECT_ID, False)
            self._showWidgets(PROJECT_FOLDER, False)
            return

        if self.data.isNational():
            options = self.data.getNationalProjects()
        else:
            options = []

        self.projIdCombo.config(values=options)

        projId = self.data.getProjectId()

        if projId is None:
            self._showWidgets(PROJECT_FOLDER, False)
            self._setVarValue(PROJECT_ID, '')
            self._setVarValue(PROJECT_FOLDER, self.data.error)
            self._showWidgets(PROJECT_ID, True)
            return

        # If we are in a national project, let's load the order details
        self.data.loadOrderDetails()
        self._setVarValue(PROJECT_ID, projId)
        self._setVarValue(PROJECT_FOLDER, self.data.getProjectFolder())
        self._showWidgets(PROJECT_ID, True)
        self._showWidgets(PROJECT_FOLDER, True)
        self._setVarValue(SCIPION_PROJECT, self.data.getScipionProjectFolder())

    def _onUserChanged(self, *args):
        username = self._getVarValue(USER_NAME)
        if not username:
            return

        user = self.data.getUserFromStr(username)
        self.data.selectUser(user)
        self._updateUserInfo(user)

    def _updateUserInfo(self, user):
        self._showWidgets(PROJECT_TYPE, user.isStaff)
        self._updateData()

    def _onProjectTypeChanged(self, *args):
        projectType = self._getVarValue(PROJECT_TYPE)

        if not projectType:
            return

        self.data.selectProjectType(projectType)
        self._updateData()

    def _onProjectChanged(self, *args):
        projectId = self._getVarValue(PROJECT_ID)
        print("_onProjectChanged:", projectId)
        if not projectId:
            return

        self.data.setProjectId(projectId)
        self._updateData()

    def _onMicroscopeChanged(self, *args):
        self.microscope = self._getVarValue(MICROSCOPE)
        self.camCombo.selection_clear()
        options = MIC_CAMERAS[self.microscope]
        self.camCombo.config(values=options)
        self._setVarValue(CAMERA, options[0])