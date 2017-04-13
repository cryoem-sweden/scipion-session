
import json

from base import DataObject


class Order(DataObject):
    # List of attributes that will be set as UString
    ATTR_STR = ['name', 'status', 'title', 'iuid', 'tags', 'modified',
                'fields', 'ownerEmail']
    # List of attributes that will be set with the type they come
    ATTR_RAW = ['history', 'owner']


def loadOrders(jsonFile):
    """ Load a list of order objects from a given json file.
    """
    dataFile = open(jsonFile)

    data = json.load(dataFile)

    print type(data)
    for k, v in data.iteritems():
        print "key: %s, type: %s" % (k, type(v))

    if 'items' not in data:
        raise Exception('Expecting a "items" section in data dict. ')

    items = data['items']

    orders = []
    for i, u in enumerate(items):
        # Get only the name of the status
        u['status'] = u['status']['name']
        # Extract owner email
        u['ownerEmail'] = u['owner']['email']
        orders.append(Order(**u))
        #pwutils.prettyDict(u)

    dataFile.close()

    return orders


def groupOrdersBy(orders, attributeName):
    groupDict = {}

    for o in orders:
        value = o.getAttributeValue(attributeName)

        if value not in groupDict:
            groupDict[value] = []

        groupDict[value].append(o)

    for k, v in groupDict.iteritems():
        print "%s: %d" % (k, len(v))

    return groupDict