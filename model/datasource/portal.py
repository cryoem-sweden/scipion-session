"""
This module contains classes and utility functions to deal with users
that can book the microscope and can start a session.
"""

import json
import requests


class PortalManager:
    """ Helper class to interact with the portal system.
    """
    def __init__(self, apiJsonFile, cache=True):
        with open(apiJsonFile) as apiFile:
            apiJson = json.load(apiFile)
            self._headers = apiJson['headers']
            self._baseUrl = apiJson['baseUrl']

            # Create a cached dict with json files for url
            # to avoid make unnecessary queries in the same session
            if cache:
                self._cache = {}

    def _getUrl(self, suffix):
        return self._baseUrl + suffix

    def _fetchJsonFromUrl(self, url):
        cache = getattr(self, '_cache', None)
        cachedJson = cache.get(url, None) if cache is not None else None

        if cachedJson:
            print("Returning cached JSON for url: %s" % url)
            return cachedJson

        print("Retrieving url: %s" % url)
        response = requests.get(url, headers=self._headers)

        if response.status_code != 200:
            print(response.status_code)
            return None
        else:
            result = response.json()
            if cache is not None:
                cache[url] = result
            return result

    def _fetchJsonFromUrlSuffix(self, suffix):
        return self._fetchJsonFromUrl(self._getUrl(suffix))

    def fetchOrdersJson(self):
        """ Fetch orders from the booking system. """
        return self._fetchJsonFromUrlSuffix('orders?recent=False')['items']

    def fetchOrderDetailsJson(self, orderCEM):
        return self._fetchJsonFromUrlSuffix('order/%s' % orderCEM.upper())
        #orderUrl = orderJson['links']['api']['href']
        #return self._fetchJsonFromUrl(orderUrl)

    def fetchFormDetailsJson(self, formId):
        """ Return  the JSON data about a given form. """
        return self._fetchJsonFromUrlSuffix('form/%s' % formId)

    def fetchAccountsJson(self):
        """ Retrieve the users list from the portal system. """
        return self._fetchJsonFromUrlSuffix('accounts')

