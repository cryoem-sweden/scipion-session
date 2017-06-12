"""
This module contains classes and utility functions to deal with users
that can book the microscope and can start a session.
"""

import json
import requests



class PortalManager():
    """ Helper class to interact with the portal system.
    """
    def __init__(self, apiJsonFile):
        with open(apiJsonFile) as apiFile:
            apiJson = json.load(apiFile)
            self._headers = apiJson['headers']
            self._baseUrl = apiJson['baseUrl']

    def _getUrl(self, suffix):
        return self._baseUrl + suffix

    def _fetchJsonFromUrl(self, suffix):

        response = requests.get(self._getUrl(suffix),
                                headers=self._headers)

        if response.status_code != 200:
            print(response.status_code)
            return None
        else:
            return response.json()
            ordersFile = open('data/orders.json', 'w')

    def fetchOrdersJson(self):
        """ Fetch orders from the booking system. """
        return self._fetchJsonFromUrl('orders?recent=False')['items']

    def fetchAccountsJson(self):
        """ Retrieve the users list from the portal system. """
        return self._fetchJsonFromUrl('accounts')