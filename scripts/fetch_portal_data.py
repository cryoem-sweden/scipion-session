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
from __future__ import print_function
from __future__ import absolute_import


import json

from config import *
from model.datasource.portal import PortalManager
from model.order import loadOrdersFromJson


apiJsonFile = 'data/%s' % PORTAL_API
outputFile = 'data/portal-data.json'

pMan = PortalManager(apiJsonFile)
# Fetch users from the Portal
accountJson = pMan.fetchAccountsJson()
# Fetch orders from the Portal and write to a json file
ordersJson = pMan.fetchOrdersJson()
orders = loadOrdersFromJson(ordersJson)


def writeData(ordersJson, fn):
    with open(fn, 'w') as ordersFile:
        print("Writing data JSON to file: ", fn)
        json.dump(ordersJson, ordersFile, indent=2)


data = {'orders': [], 'forms': {}, 'users': accountJson}


for o in orders:
    print("%s: %s" % (o.getId(), o.getTitle()))
    detailsJson = pMan.fetchOrderDetailsJson(o.getId())
    formId = o.form['iuid']
    if formId not in data['forms']:
        data['forms'][formId] = pMan.fetchFormDetailsJson(formId)

    data['orders'].append(detailsJson)


writeData(data, outputFile)

