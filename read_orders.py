
import pyworkflow.utils as pwutils

from model.order import loadOrders, groupOrdersBy

dataFn = 'data/orders.json'

orders = loadOrders(dataFn)

statusDict = groupOrdersBy(orders, 'ownerEmail')

for o in orders[:3]:
    o.printAll()
    print "history: "
    pwutils.prettyDict(o.history)

for k, v in statusDict.iteritems():
    print "%s: %d" % (k, len(v))
