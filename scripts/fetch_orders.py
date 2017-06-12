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

from model.order import loadOrdersFromJson


t = pwutils.Timer()

t.tic()

apiJson = json.load(open('data/api.json'))

headers = apiJson['headers']
url = apiJson['url']


response = requests.get(url, headers=headers)

if response.status_code != 200:
    print(response.status_code)
else:
    itemsJson = response.json()
    ordersFile = open('data/orders.json', 'w')
    json.dump(itemsJson, ordersFile, indent=2)
    ordersFile.close()
    allList = []

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

    allOrdersFn = 'data/orders_detailed.json'
    allFile = open(allOrdersFn, 'w')
    print "Writing orders info to: ", allOrdersFn
    json.dump(allList, allFile, indent=2)
    allFile.close()

    orders = loadOrdersFromJson(itemsJson)

    print "orders: ", len(orders)
    #print(json.dumps(response.json(), indent=2))

t.toc()
