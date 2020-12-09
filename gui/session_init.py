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
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as tkFont

import pyworkflow as pw
import pyworkflow.gui as pwgui
from pyworkflow.gui.project.base import ProjectBaseWindow
from pyworkflow.gui.widgets import HotButton, Button
from pyworkflow.gui.browser import FileBrowserWindow
from pyworkflow.gui import Message, Icon
from pyworkflow.project import ProjectSettings

from model.data import *
from .chooser import OptionChooser
from config import *


LABEL_SELECT_CEM = 'Select CEM'
LABEL_SELECT_PI = 'Select PI'
LABEL_SELECT_USER = 'Select or type user (Name -- Email)'
LABEL_NONE = 'None'


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
        self._createStatus = 'disabled'
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

        versionText = 'version: %s' % VERSION
        label2 = tk.Label(headerFrame, text=versionText,
                         font=self.bigFontBold,
                         borderwidth=0, anchor='nw',  # bg='white',
                         fg=pwgui.Color.DARK_GREY_COLOR)
        headerFrame.columnconfigure(1, weight=1)
        label2.grid(row=0, column=1, sticky='ne', padx=(20, 5), pady=10)

        # Body section
        bodyFrame = tk.Frame(self, bg='white')
        bodyFrame.grid(row=1, column=0, sticky='news')
        self._fillContent(bodyFrame)

        # Add the create project button
        btnFrame = tk.Frame(self, bg='white')
        btn = HotButton(btnFrame, text="Create New Session",
                        font=self.bigFontBold,
                        command=self._onAction,
                        state=self._createStatus)
        btn.grid(row=0, column=1, sticky='ne', padx=10, pady=10)
        self._newSessionBtn = btn

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

        def _createLabel(text, bold=False):
            boldStr = 'bold' if bold else ''
            return tk.Label(frame, text=text,
                            font="helvetica 12 %s" % boldStr, bg='white')

        def __addLabeledWidget(text, widget=None, pady=5, bold=False):
            label = _createLabel(text, bold)
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

        def _getSessionAction():
            micIndex = self._micChooser.getSelectedIndex()
            if micIndex is None:
                return "Select Microscope"

            camIndex = self._switchCam.widgets[micIndex].getSelectedIndex()
            if camIndex is None:
                return "Select Camera"

            resourceId = self._micChooser.getSelectedIndex() + 1
            if resourceId in self._bookings:
                b = self._bookings[resourceId]
                values = {'CEM': b['application_code'],
                          'Owner': b['owner']['name'],
                          'Creator': b['creator']['name']
                          }
            else:
                values = {}
                b = None

            for k, v in self._textVars.items():
                v.set(values.get(k, '-'))

            self._current_booking = b
            if b is None:
                return ("There is no booking for this microscope. "
                        "Check the booking system. ")

            return None

        def _checkSessionAction():
            action = _getSessionAction()

            if action is None:
                msg = self._createSession().getId()
            else:
                msg = action

            self._sessionLabel.config(fg='red' if action else 'green')
            self._sessionVar.set(msg)
            self._createStatus = 'disabled' if action else 'normal'
            btn = getattr(self, '_newSessionBtn', None)
            if btn is not None:
                btn.config(state=self._createStatus)

        class Switcher(tk.Frame):
            def __init__(self, *args, **kwargs):
                tk.Frame.__init__(self, *args, **kwargs)
                self._index = -1
                self.widgets = []

            def add(self, widget):
                self.widgets.append(widget)

            def set(self, i):
                if i < 0 or i >= len(self.widgets):
                    raise Exception("Invalid index")

                if self._index >= 0:
                    self.widgets[self._index].grid_forget()

                self.widgets[i].grid(row=0, column=0, sticky='news')
                self._index = i

        def _showCameraOptions(chooser):
            """ Show the correct camera options depending on the
            selected microscope. """
            i = chooser.getSelectedIndex()
            self._switchCam.set(i)
            _checkSessionAction()

        def _onChange(*args):
            if hasattr(self, '_sessionLabel'):
                _checkSessionAction()

        def _onChangePreprocessing(*args):
            """ Called when the selection is changed. """
            i = self._prepChooser.getSelectedIndex()
            self._switchPre.set(i)

        EXTRA_PAD = 30

        f1 = OptionChooser(frame, bg='white', optionWidth=200)
        f1.onSelectionChanged(_showCameraOptions)
        f1.addOption('Krios α', self.data.getResourceFile("titan_small.gif"))
        f1.addOption('Krios β', self.data.getResourceFile("titan_small.gif"))
        f1.addOption('Talos', self.data.getResourceFile("talos_small.gif"))
        __addLabeledWidget("Microscope", f1, bold=True)
        self._micOrder = {TITAN_A: 0, TITAN_B: 0, TALOS: 2}
        self._micChooser = f1
        self._switchCam = Switcher(frame)

        def _addCamChooser(*options):
            oc = OptionChooser(self._switchCam, bg='white', optionWidth=200)
            for o in options:
                oc.addOption(o)
            self._switchCam.add(oc)
            oc.selectIndex(0)
            oc.onSelectionChanged(_onChange)

        for mic in MICROSCOPES:
            _addCamChooser(*MIC_CAMERAS[mic])

        #camChoosers = [_createChooser(*MIC_CAMERAS[mic]) for mic in MICROSCOPES]
        # f2 = camChoosers[0]
        # self._camRow = self._lastRow
        __addLabeledWidget("Camera", self._switchCam)

        # --------- Load some data ---------------
        from emhub.client import DataClient
        from emhub.utils import datetime_to_isoformat

        apiJsonFile = getDataFile('api.json')
        with open(apiJsonFile) as f:
            apiJson = json.load(f)

        dc = DataClient(apiJson['emhub']['url'])
        dc.login(apiJson['emhub']['user'],
                 apiJson['emhub']['password'])

        start = datetime_to_isoformat(self.data.date.replace(hour=0))
        end = datetime_to_isoformat(self.data.date.replace(hour=23, minute=59))
        r = dc.request('get_bookings_range', jsonData={'start': start, 'end': end})
        self._bookings = {b['resource']['id']: b for b in r.json()
                          if b['type'] == 'booking'}

        users = {}

        def get_user(user_id):
            if user_id not in users:
                r = dc.request('get_users', jsonData={'condition': 'id=%s' % user_id})

                users[user_id] = r.json()[0]

            return users[user_id]

        def get_application_code(b):
            # Take only the first part of the application label
            # (because it can contains the alias in parenthesis)
            m = re.search("\([^,]+(,([^,]*))\)", b['title'])
            return 'fac' if m is None else m.group(2).upper().strip()

        for b in self._bookings.values():
            b['owner'] = get_user(b['owner']['id'])
            b['creator'] = get_user(b['creator']['id'])
            b['application_code'] = get_application_code(b)

        dc.logout()

        self._textVars = {}

        def _addLabeledText(label, text):
            var = tk.StringVar()
            var.set(text)
            labelWidget = _createLabel(text)
            labelWidget.config(textvariable=var)
            self._textVars[label] = var
            __addLabeledWidget(label, labelWidget, bold=True)

        _addLabeledText("CEM", '')
        _addLabeledText("Owner", '')
        _addLabeledText("Creator", '')

        # --------- Session block ----------------
        self._sessionVar = tk.StringVar()
        self._sessionLabel = tk.Label(frame, textvariable=self._sessionVar,
                                      bg='white', fg='red')

        __addLabeledWidget("Session ID", self._sessionLabel,
                           pady=(EXTRA_PAD, 0), bold=True)

        # --------- Preprocessing block ----------------
        f4 = OptionChooser(frame, bg='white', optionWidth=200)
        f4.addOption('Scipion', self.data.getResourceFile("scipion_logo.gif"))
        f4.addOption('Scipion (custom)', self.data.getResourceFile("scipion_logo.gif"))
        f4.addOption(LABEL_NONE, self.data.getResourceFile("none.gif"))
        f4.onSelectionChanged(_onChangePreprocessing)
        self._prepChooser = f4
        __addLabeledWidget("Pre-processing", f4, pady=(EXTRA_PAD, 0), bold=True)

        self._switchPre = Switcher(frame, bg='white')

        def _addFrame():
            preFrame = tk.Frame(self._switchPre, bg='white')
            self._switchPre.add(preFrame)
            return preFrame

        preFrame1 = _addFrame()
        preOptions = [
            ("Motion correction", ['relion - motioncor', 'motioncor2']),
            ("CTF estimation", ['ctffind4', 'gctf'])
        ]
        self._preDict = {}

        for row, (text, options) in enumerate(preOptions):
            label = tk.Label(preFrame1, text=text, font="helvetica 12", bg='white')
            label.grid(row=row, column=0, sticky='ne')

            v = tk.StringVar()

            for i, o in enumerate(options):
                rb = tk.Radiobutton(preFrame1, text=o, variable=v, value=o, bg='white')
                rb.grid(row=row, column=i+1, sticky='nw')

            v.set(options[0])
            self._preDict[text] = v

        preFrame2 = _addFrame()
        self._workflowVar = tk.StringVar()
        entry = ttk.Entry(preFrame2, width=50, textvariable=self._workflowVar)
        entry.grid(column=0, row=0)

        def _onChoose(fileInfo):
            self._workflowVar.set(fileInfo.getPath())

        def _chooseWorkflow():
            browser = FileBrowserWindow("Select the one of the predefined MTF files",
                                        self.windows, getDataFile('workflows'), onSelect=_onChoose)
            browser.show()

        button = Button(preFrame2, text="Browse", command=_chooseWorkflow)
        button.grid(column=1, row=0)

        preFrame3 = _addFrame()

        __addLabeledWidget('', self._switchPre)

        f4.selectIndex(0)
        f1.selectIndex(self._micOrder[self.data.microscope])
        # Select Scipion as default for pre-processing
        _checkSessionAction()

    def _createSession(self):
        micIndex = self._micChooser.getSelectedIndex()
        microscope = MICROSCOPES[micIndex]
        camIndex = self._switchCam.widgets[micIndex].getSelectedIndex()
        camera = MIC_CAMERAS[microscope][camIndex]
        b = self._current_booking

        def getPerson(key):
            p = b[key]
            return Person(name=p['name'], email=p['email'])

        appLabel = b['application_code'].lower()

        if appLabel.startswith('cem'):
            projectType = PROJ_NATIONAL
        elif appLabel.startswith('dbb'):
            projectType = PROJ_INTERNAL
        else:
            projectType = PROJ_FACILITY

        prepText = self._prepChooser.getSelectedText()

        preprocessing = None

        if prepText.startswith("Scipion"):
            if 'custom' in prepText:
                preprocessing = {'workflow': self._workflowVar.get()}
            else:
                prepValues = {k:self._preDict[k].get() for k in self._preDict.keys()}
                preprocessing = {'options': prepValues}

        session = self.data.createSession(microscope, camera, projectType,
                                          cem=appLabel,
                                          pi=getPerson('owner'),
                                          user=getPerson('owner'),
                                          operator=getPerson('creator'),
                                          preprocessing=preprocessing
                                          )
        return session

    def _onAction(self, e=None):
        try:
            session = self._createSession()
            self.data.storeSession(session)

            if session.getScipionProjectName():
                os.system('scipion project %s &'
                          % session.getScipionProjectName())

            self.windows.close()

        except Exception as e:
            import traceback
            traceback.print_exc(file=sys.stdout)
            self.windows.showError("*Error*: %s" % e)

