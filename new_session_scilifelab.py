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
# *  e-mail address 'delarosatrevin@scilifelab.se'
# *
# **************************************************************************

import os
import sys
import argparse
import datetime as dt

from config import *
from model.data import Data
from gui.session_init import BoxWizardWindow


def parseDate(dateStr):
    """ Get date from YYYY/MM/DD string """
    year, month, day = dateStr.split('/')
    return dt.datetime(year=int(year), month=int(month), day=int(day))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Query reservations. ")
    add = parser.add_argument  # shortcut
    add('--microscope', help="Select microscope", default='titan')
    add('--day', help="Date to check for reservations (Today by default)")
    args = parser.parse_args()

    # Assume the data folder is in the same place as this script
    dataArgs = {'dataFolder': os.path.join(os.path.dirname(__file__), 'data'),
                'microscope': MICROSCOPES_ALIAS[args.microscope.lower()],
                'date': parseDate(args.day) if args.day else dt.datetime.now()
                }

    data = Data(**dataArgs)

    wizWindow = BoxWizardWindow(data=data)
    wizWindow.show()
