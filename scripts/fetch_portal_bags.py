"""Try accessing the API.
NOTE: You need to change several items in this script to make it work:
- The domain name must match your instance.
- The API key is set for your account; see your account page.
- The order IUID need to be changed, of course.
NOTE: This uses the third-party 'requests' module, which is much nicer than
the standard 'urllib' module.
"""

import json
from config import *

import pyworkflow.utils as pwutils

from model.datasource.portal import PortalManager
from model.order import loadActiveBags, loadAccountsFromJson

t = pwutils.Timer()

t.tic()

apiJsonFile = 'data/%s' % PORTAL_API

pMan = PortalManager(apiJsonFile)

# Load list of PIs
piList = loadAccountsFromJson(pMan.fetchAccountsJson(), isPi=False)
piSet = set(pi['email'] for pi in piList)

for pi in piList:
    name = "%s %s" % (pi['first_name'], pi['last_name'])
    print "%25s" % name, pi['email']

# Load active bags
bags = loadActiveBags(pMan)

for o in bags:
    print "%s: %s" % (o.getId(), o.getTitle())
    details = pMan.fetchOrderDetailsJson(o.getId())
    piList = details['fields']['pi_list']
    for name, email in piList:
        suffix = '' if email.lower() in piSet else "  (NOT REGISTERED IN PORTAL)"
        print "   ", name, email, suffix

t.toc()