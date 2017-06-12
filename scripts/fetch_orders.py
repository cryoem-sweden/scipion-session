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

import pyworkflow.utils as pwutils

from model.datasource.portal import PortalManager
from model.order import loadOrdersFromJson


t = pwutils.Timer()

t.tic()

apiJsonFile = 'data/portal-api.json'

pMan = PortalManager(apiJsonFile)

# Fetch orders from the Portal and write to a json file
ordersJson = pMan.fetchOrdersJson()
ordersFile = open('data/test-portal-orders.json', 'w')
json.dump(ordersJson, ordersFile, indent=2)
ordersFile.close()
orders = loadOrdersFromJson(ordersJson)
print "Orders: ", len(orders)

# Fetch orders from the Portal
accountsJson = pMan.fetchAccountsJson()
accountsFile = open('data/test-portal-accounts.json', 'w')
json.dump(accountsJson, accountsFile, indent=2)
accountsFile.close()
print "Accounts: ", len(accountsJson['items'])

# The following code get more info for each order
#allList = []
# for item in itemsJson['items']:
#     orderUrl = item['links']['api']['href']
#     cemCode = item['identifier']
#     print "Downloading order: ", cemCode
#     response = requests.get(orderUrl, headers=headers)
#     orderJson = response.json()
#     # orderFile = open('data/orders/%s.json' % cemCode, 'w')
#     # json.dump(orderJson, orderFile, indent=2)
#     # orderFile.close()
#     allList.append(orderJson)

# allOrdersFn = 'data/orders_detailed.json'
# allFile = open(allOrdersFn, 'w')
# print "Writing orders info to: ", allOrdersFn
# json.dump(allList, allFile, indent=2)
# allFile.close()



t.toc()
