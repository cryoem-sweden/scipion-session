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


import argparse
import json

import pyworkflow.utils as pwutils
from config import *
from model.datasource.portal import PortalManager
from model.order import loadOrdersFromJson

parser = argparse.ArgumentParser()
_addArg = parser.add_argument  # short notation

_addArg("--details", type=str, default='',
        dest='detailsCem', metavar='CEM',
        help="Provide the CEM code to print details of this order")

_addArg("--detailed", action='store_true',
        help="If you provide this option the detailed list will be written")

_addArg("--sort", type=str, default='cem',
        dest='sort', metavar='SORT',
        help="Sort criteria. (cem, date)")

_addArg("--filter", type=str, default='',
        dest='filter', metavar='SORT',
        help="Filter orders base on some criteria. (bag)")

args = parser.parse_args()

t = pwutils.Timer()

t.tic()

apiJsonFile = 'data/%s' % PORTAL_API

pMan = PortalManager(apiJsonFile)


def writeOrders(ordersJson, fn):
    with open(fn, 'w') as ordersFile:
        print("Writing orders JSON to file: ", fn)
        json.dump(ordersJson, ordersFile, indent=2)


if not  args.detailsCem:
    # Fetch orders from the Portal and write to a json file
    ordersJson = pMan.fetchOrdersJson()
    ordersFn = 'data/%s' % PORTAL_ORDERS
    writeOrders(ordersJson, ordersFn)
    orders = loadOrdersFromJson(ordersJson)

    filter = args.filter
    if filter:
        if filter == 'bag':
            filterFunc = lambda o: o.isBag() and o.getStatus() == 'accepted'
        else:
            raise Exception("Invalid value for filter: %s" % filter)
        orders = [o for o in orders if filterFunc(o)]

    sort = args.sort
    if sort:
        if sort == 'cem':
            keyFunc = lambda o: o.getId()
        elif sort == 'date':
            keyFunc = lambda o: o.getId()
        elif sort == 'pi':
            keyFunc = lambda o: o.getPiEmail()
        else:
            raise Exception("Invalid value for sort: %s" % sort)
        orders = sorted(orders, key=keyFunc)

    ordersDetailed = []

    for o in orders:
        print("%s: %s" % (o.getId(), o.getTitle()))
        if args.detailed:  
            detailsJson = pMan.fetchOrderDetailsJson(o.getId())
            ordersDetailed.append(detailsJson)

    if ordersDetailed:
        writeOrders(ordersDetailed, ordersFn.replace('.json', '-detailed.json'))

    print("Orders: ", len(orders))

else:
    orderId = args.detailsCem
    print("Retrieving details for first order: ", orderId)
    orderDetailsJson = pMan.fetchOrderDetailsJson(orderId)
    print(json.dumps(orderDetailsJson, indent=2))


t.toc()
