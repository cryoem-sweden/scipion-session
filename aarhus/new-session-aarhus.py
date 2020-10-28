#!/usr/bin/env python
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

import sys, os
from datetime import datetime

from pyworkflow.manager import Manager
from pyworkflow.gui.project import ProjectWindow
import pyworkflow.utils as pwutils


def usage(error):
    print("""
    ERROR: %s
    
    Usage: scipion python new-session-aarhus.py workflow.json PROJECT_FOLDER

    """ % error)
    sys.exit(1)    

n = len(sys.argv)

if n < 2 or n > 3:
    usage("Incorrect number of input parameters")

scipionProjPath = sys.argv[2] if n == 3 else None
    
jsonFn = os.path.abspath(sys.argv[1])

now = datetime.now()
projName = "scipion-%s" % now.strftime('%Y%m%d-%H%M%S')

print("Creating project: ", projName)
 
# Create a new project
manager = Manager()
proj = manager.createProject(projName, location=scipionProjPath)
projPath = manager.getProjectPath(projName)
proj.loadProtocols(jsonFn)

projWindow = ProjectWindow(projPath)
projWindow.show()


