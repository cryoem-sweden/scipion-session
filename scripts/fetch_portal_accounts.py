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

# Fetch orders from the Portal and write to a json file
accountsFn = 'data/%s' % PORTAL_ACCOUNTS
with open(accountsFn, 'w') as ordersFile:
    print("Writing orders JSON to file: %s" % accountsFn)
    json.dump(accountJson, ordersFile, indent=2)

piList = loadAccountsFromJson(accountJson, isPi=True)#, university='SU')

headers = ["First Name", "Last Name", "Email", "Univ.", "PI", "Invoice REF"]
row_format = u"{:<15}{:<15}{:<35}{:<5}{:<5}{:<20}"
print(row_format.format(*headers))

for u in piList:
    row = [u['first_name'], u['last_name'],
           u['email'], u['university'], u['pi'], u['invoice_ref']
           ]
    print(row_format.format(*['"%s",' % r for r in row]))

print("Accounts: ", len(piList))


t.toc()
