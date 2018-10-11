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
import Tkinter as tk
import ttk
import tkFont

import pyworkflow as pw
import pyworkflow.gui as pwgui
from pyworkflow.gui.project.base import ProjectBaseWindow
from pyworkflow.gui.widgets import HotButton, Button
from pyworkflow.gui import Message, Icon
from pyworkflow.config import ProjectSettings

from model.data import *
from chooser import OptionChooser
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
                        state='disabled')
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

        def _getSessionAction():
            def checkPiAndUser():
                if self._piCombo.var.get() == LABEL_SELECT_PI:
                    return LABEL_SELECT_PI

                userValue = self._userCombo.var.get()
                if not userValue or not self._isValidUserStr(userValue):
                    return LABEL_SELECT_USER

            def checkOperator():
                operator = self._operatorCombo.var.get()
                if not self._isValidUserStr(operator):
                    return "Select operator"

            mic = self._micChooser.getSelectedIndex()
            if mic is None:
                return "Select Microscope"

            cam = self._camChoosers[mic].getSelectedIndex()
            if cam is None:
                return "Select Camera"

            proj = self._projectChooser.getSelectedIndex()
            if proj is None:
                return "Select Project"

            if proj == PROJ_NATIONAL:
                if self._cemCombo.var.get() == LABEL_SELECT_CEM:
                    return LABEL_SELECT_CEM
                return checkPiAndUser() or checkOperator()
            elif proj == PROJ_INTERNAL:
                return checkPiAndUser()
            else:
                return checkOperator()

            return None

        def _checkSessionAction():
            action = _getSessionAction()

            if action is None:
                msg = self._createSession().getId()
            else:
                msg = action

            self._sessionLabel.config(fg='red' if action else 'green')
            self._sessionVar.set(msg)
            btn = getattr(self, '_newSessionBtn', None)
            if btn is not None:
                btn.config(state='disabled' if action else 'normal')

        def _showCameraOptions(chooser):
            """ Show the correct camera options depending on the
            selected microscope. """
            i = chooser.getSelectedIndex()
            j = 1 - i  # old index, this works only for two values
            self._camChoosers[j].grid_forget()
            camChooser = self._camChoosers[i]
            camChooser.grid(row=self._camRow, column=1, sticky='nw', pady=5, padx=5)

            _checkSessionAction()

        def _configCombo(combo, selection='', values=[]):
            combo.set(selection)
            if values is not None:
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
            cemConfig = {'selection': LABEL_NONE}

            i = chooser.getSelectedIndex()
            # 0 is National, 1 is Internal, 2 Facility
            if i == PROJ_NATIONAL:
                piConfig = {'selection': 'Select CEM code first'}
                cemConfig = {'selection': LABEL_SELECT_CEM,
                             'values': self._bagsDict.keys()}
            elif i == PROJ_INTERNAL:
                # List of internal PIs of SU
                piFilter = lambda a: a['pi'] and a['university'] == 'SU'
                piConfig = {'selection': LABEL_SELECT_PI,
                            'values': _getAccountList(piFilter)}
                _configCombo(self._operatorCombo, values=None)
            elif i == PROJ_FACILITY:
                piConfig['selection'] = LABEL_NONE
            else:
                raise Exception('Invalid option for project type %s' % i)

            _configCombo(self._piCombo, **piConfig)
            _configCombo(self._cemCombo, **cemConfig)
            _configCombo(self._userCombo)
            _checkSessionAction()

        def _onSelectCEM(*args):
            bag = self._bagsDict.get(self._cemCombo.var.get(), None)
            _configCombo(self._piCombo,
                         selection=LABEL_SELECT_PI,
                         values=['%s -- %s' % tuple(pi) for pi in bag.piList])
            _checkSessionAction()

        def _onSelectPI(*args):
            piEmail = _getEmailFromCombo(self._piCombo)
            userFilter = lambda a: a['invoice_ref'] == piEmail
            _configCombo(self._userCombo, values=_getAccountList(userFilter))
            _checkSessionAction()

        def _onChange(*args):
            if hasattr(self, '_sessionLabel'):
                _checkSessionAction()

        EXTRA_PAD = 30

        f1 = OptionChooser(frame, bg='white', optionWidth=200)
        f1.onSelectionChanged(_showCameraOptions)
        f1.addOption('Krios 1', self.data.getResourceFile("titan_small.gif"))
        f1.addOption('Talos', self.data.getResourceFile("talos_small.gif"))
        __addLabeledWidget("Microscope", f1, bold=True)
        self._micOrder = {TITAN: 0, TALOS: 1}
        self._micChooser = f1

        f2 = OptionChooser(frame, bg='white', optionWidth=200)
        f2.onSelectionChanged(_onChange)
        f2.addOption('K2')
        f2.addOption('Falcon 3')
        self._camRow = self._lastRow
        __addLabeledWidget("Camera", f2)

        f2b = OptionChooser(frame, bg='white', optionWidth=200)
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
        self._projectChooser = f3
        __addLabeledWidget("Project", f3, pady=(EXTRA_PAD, 0), bold=True)

        self._cemCombo = __createCombobox([], callback=_onSelectCEM, width=11)
        __addLabeledWidget("CEM code", self._cemCombo)

        self._piCombo = __createCombobox([], callback=_onSelectPI)
        __addLabeledWidget("PI", self._piCombo)

        self._userCombo = __createCombobox([], readOnly=False,
                                           callback=_onChange)
        self._userCombo.var.trace('w', _onChange)

        __addLabeledWidget("User", self._userCombo)

        self._operatorCombo = __createCombobox(STAFF,
                                               callback=_onChange)
        __addLabeledWidget("Operator", self._operatorCombo)

        f4 = OptionChooser(frame, bg='white', optionWidth=200)
        f4.addOption('Scipion', self.data.getResourceFile("scipion_logo.gif"))
        f4.addOption(LABEL_NONE, self.data.getResourceFile("none.gif"))
        self._prepChooser = f4

        # --------- Session block ----------------
        self._sessionVar = tk.StringVar()
        self._sessionLabel = tk.Label(frame, textvariable=self._sessionVar,
                                      bg='white', fg='red')

        __addLabeledWidget("Session ID", self._sessionLabel,
                           pady=(EXTRA_PAD, 0), bold=True)

        # --------- Preprocessing block ----------------
        __addLabeledWidget("Pre-processing", f4, pady=(EXTRA_PAD, 0), bold=True)

        # Select Krios, TESTING
        data = self.data
        f1.selectIndex(self._micOrder[data.microscope])
        # Select Scipion as default for pre-processing
        f4.selectIndex(0)

        r = data.reservation
        if r is not None:
            r.printAll()
            cem = r.getCemCode()
            if cem:
                self._projectChooser.selectIndex(PROJ_NATIONAL)
                if cem.upper() in self._bagsDict:
                    self._cemCombo.var.set(cem.upper())
                    _onSelectCEM()
            u = r.user
            foundUser = False
            if u is not None:
                for i, operator in enumerate(STAFF):
                    if u.email.get() in operator:
                        self._operatorCombo.var.set(operator)
                        _onChange()
                        foundUser = True
                if not foundUser:
                    self._projectChooser.selectIndex(PROJ_INTERNAL)
                    _onChangeProjectType(self._projectChooser)
            #_checkSessionAction()

    def _isValidUserStr(self, userStr):
        """ Valid user string is:  Name -- email """
        parts = userStr.split('--')
        return (len(parts) == 2 and all(p.strip() for p in parts)
                and all(c in parts[1] for c in '.@'))

    def _createSession(self):
        mic = self._micChooser.getSelectedIndex()
        microscope = MICROSCOPES[mic]
        camera = MIC_CAMERAS[microscope][self._camChoosers[mic].getSelectedIndex()]
        projectType = self._projectChooser.getSelectedIndex()

        def _getPersonFromCombo(combo):
            value = combo.var.get()
            if self._isValidUserStr(value):
                name, email = value.split('--')
                return Person(name=name.strip(), email=email.strip())
            else:
                return None

        session = self.data.createSession(microscope, camera, projectType,
                                          cem=self._cemCombo.var.get(),
                                          pi=_getPersonFromCombo(self._piCombo),
                                          user=_getPersonFromCombo(self._userCombo),
                                          operator=_getPersonFromCombo(self._operatorCombo),
                                          preprocessing=self._prepChooser.getSelectedText()
                                          )
        return session

    def _onAction(self, e=None):
        try:
            session = self._createSession()
            self.data.storeSession(session)

            if session.getScipionProjectName():
                os.system('%s project %s &'
                          % (pw.getScipionScript(),
                             session.getScipionProjectName()))

            self.windows.close()

        except Exception as e:
            import traceback
            traceback.print_exc(file=sys.stdout)
            self.windows.showError("*Error*: %s" % e)

