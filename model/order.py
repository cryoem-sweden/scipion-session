
import json

from base import DataObject


class Order(DataObject):
    # List of attributes that will be set as UString
    ATTR_STR = ['identifier', 'status', 'title', 'iuid', 'tags', 'modified',
                'fields', 'ownerEmail']
    # List of attributes that will be set with the type they come
    ATTR_RAW = ['history', 'owner', 'fields', 'form']

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

    def getInvoiceReference(self):
        return self.fields.get('invoice_reference', None)

    def isBag(self):
        return 'BAG application form' in self.form['title']

    def getStatus(self):
        return self.status.get()


def loadOrders(jsonFile='data/orders.json'):
    """ Load a list of order objects from a given json file.
    """
    dataFile = open(jsonFile)
    orders = loadOrdersFromJson(json.load(dataFile))
    dataFile.close()
    return orders


def loadOrdersFromJson(ordersJson):
    orders = []
    for i, u in enumerate(ordersJson):
        # Get only the name of the status
        # print u['status'], type(u['status'])
        # u['status'] = u['status']['name']
        # Extract owner email
        u['ownerEmail'] = u['owner']['email']
        orders.append(Order(**u))

    return orders


def loadActiveBags(pMan):
    """ Return the list of orders that are active bags
    and also set the list of PIs.
    """
    # FIXME: Now we are assuming only the 'BAG application form'
    # are active, it will be good to have another way to distinguish
    # active one, MAYBE CLOSE THE FINISHED applications?

    ordersJson = pMan.fetchOrdersJson()
    filterFunc = lambda o: o.isBag() and o.getStatus() == 'accepted'
    orders = list(filter(filterFunc, loadOrdersFromJson(ordersJson)))

    for o in orders:
        details = pMan.fetchOrderDetailsJson(o.getId())
        o.piList = details['fields']['pi_list']

    return orders


def groupOrdersBy(orders, attributeName):
    groupDict = {}

    for o in orders:
        value = o.getAttributeValue(attributeName)

        if value not in groupDict:
            groupDict[value] = []

        groupDict[value].append(o)

    return groupDict


# -------------------- Account related functions --------------------------------

def loadAccountsFromJson(accountsJson, isPi=True, university=None):
    filter = lambda a: ((a['pi'] or not isPi) and
                        (a['university'] == university or university is None))
    return [a for a in accountsJson['items'] if filter(a)]


