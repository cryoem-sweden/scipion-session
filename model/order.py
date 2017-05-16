
import json

from base import DataObject


class Order(DataObject):
    # List of attributes that will be set as UString
    ATTR_STR = ['identifier', 'status', 'title', 'iuid', 'tags', 'modified',
                'fields', 'ownerEmail']
    # List of attributes that will be set with the type they come
    ATTR_RAW = ['history', 'owner', 'fields']

    def getId(self):
        """ Return CEM code """
        return self.identifier.get().lower()

    def getTitle(self):
        return self.title.get()

    def getPi(self):
        return self.fields['project_pi']

    def getPiEmail(self):
        return self.fields['pi_email']

    def getInvoiceAddress(self):
        return self.fields['project_invoice_addess']


def loadOrders(jsonFile='data/orders.json'):
    """ Load a list of order objects from a given json file.
    """
    dataFile = open(jsonFile)

    data = json.load(dataFile)

    #if 'items' not in data:
    #    raise Exception('Expecting a "items" section in data dict. ')

    #items = data['items']
    items = data

    orders = []
    for i, u in enumerate(items):
        # Get only the name of the status
        #print u['status'], type(u['status'])
        #u['status'] = u['status']['name']
        # Extract owner email
        u['ownerEmail'] = u['owner']['email']
        orders.append(Order(**u))

    dataFile.close()

    return orders


def groupOrdersBy(orders, attributeName):
    groupDict = {}

    for o in orders:
        value = o.getAttributeValue(attributeName)

        if value not in groupDict:
            groupDict[value] = []

        groupDict[value].append(o)

    return groupDict
