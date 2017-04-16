
import pyworkflow.utils as pwutils

from model.order import loadOrders, groupOrdersBy

dataFn = 'data/orders.json'

orders = loadOrders(dataFn)

statusDict = groupOrdersBy(orders, 'ownerEmail')



for o in sorted(orders, key=lambda o: o.name.get()):
    if o.status == 'accepted':
        o.printAll()
        print "history: "
        pwutils.prettyDict(o.history)
        print "owner: "
        pwutils.prettyDict(o.owner)

#for k, v in statusDict.iteritems():
#    print "%s: %d" % (k, len(v))
