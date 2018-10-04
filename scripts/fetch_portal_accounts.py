"""Try accessing the API.
NOTE: You need to change several items in this script to make it work:
- The domain name must match your instance.
- The API key is set for your account; see your account page.
- The order IUID need to be changed, of course.
NOTE: This uses the third-party 'requests' module, which is much nicer than
the standard 'urllib' module.
"""

import json
import requests
from config import *

import pyworkflow.utils as pwutils

from model.datasource.portal import PortalManager
from model.order import loadAccountsFromJson


t = pwutils.Timer()

t.tic()

apiJsonFile = 'data/%s' % PORTAL_API

pMan = PortalManager(apiJsonFile)

# Fetch users from the Portal
accountJson = pMan.fetchAccountsJson()
#print json.dumps(accountJson, indent=2)

piList = loadAccountsFromJson(accountJson, university='SU')

for u in piList:
    print("%s %s - %s (%s) %s"
          % (u['first_name'],
             u['last_name'],
             u['email'],
             u['university'],
             u['pi']
             )
          )

print "Total PIs: ", len(piList)


"""
  "items": [
    {
      "status": "enabled",
      "first_name": "Annemarie",
      "last_name": "Perez",
      "name": "Perez, Annemarie",
      "links": {
        "api": {
          "href": "https://cryoem.scilifelab.se/api/v1/account/a.perezboerema%40scilifelab.se"
        },
        "display": {
          "href": "https://cryoem.scilifelab.se/account/a.perezboerema%40scilifelab.se"
        }
      },
      "gender": "female",
      "university": "SU",
      "modified": "2016-08-31T11:20:47.441Z",
      "orders": {
        "count": 0,
        "links": {
          "api": {
            "href": "https://cryoem.scilifelab.se/api/v1/account/a.perezboerema%40scilifelab.se/orders"
          },
          "display": {
            "href": "https://cryoem.scilifelab.se/account/a.perezboerema%40scilifelab.se/orders"
          }
        }
      },
      "invoice_address": {
        "country": "AF",
        "city": "",
        "zip": "",
        "address": ""
      },
      "role": "user",
      "address": {
        "country": "SE",
        "city": "",
        "zip": "",
        "address": ""
      },
      "invoice_ref": "",
      "login": "2016-08-31T11:20:47.441Z",
      "pi": false,
      "email": "a.perezboerema@scilifelab.se"
    },
"""

t.toc()
