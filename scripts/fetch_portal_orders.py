"""Try accessing the API.
NOTE: You need to change several items in this script to make it work:
- The domain name must match your instance.
- The API key is set for your account; see your account page.
- The order IUID need to be changed, of course.
NOTE: This uses the third-party 'requests' module, which is much nicer than
the standard 'urllib' module.
"""

import argparse
import json
from config import *

import pyworkflow.utils as pwutils

from model.datasource.portal import PortalManager
from model.order import loadOrdersFromJson

parser = argparse.ArgumentParser()
_addArg = parser.add_argument  # short notation

_addArg("--details", type=str, default='',
        dest='detailsCem', metavar='CEM',
        help="Provide the CEM code to print details of this order")

_addArg("--list", action="store_true",
        help="List current orders")

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

if args.list:
    # Fetch orders from the Portal and write to a json file
    ordersJson = pMan.fetchOrdersJson()
    ordersFn = 'data/%s' % PORTAL_ORDERS
    ordersFile = open(ordersFn, 'w')
    print "Writing orders JSON to file: %s" % ordersFn
    json.dump(ordersJson, ordersFile, indent=2)
    ordersFile.close()
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

    for o in orders:
        print "%s: %s" % (o.getId(), o.getTitle())
        details = pMan.fetchOrderDetailsJson(o.getId())
        piList = details['fields']['pi_list']
        for name, email in piList:
            print "   ", name, email


    print "Orders: ", len(orders)

elif args.detailsCem:
    orderId = args.detailsCem
    print "Retrieving details for first order: ", orderId
    orderDetailsJson = pMan.fetchOrderDetailsJson(orderId)
    print json.dumps(orderDetailsJson, indent=2)


t.toc()
