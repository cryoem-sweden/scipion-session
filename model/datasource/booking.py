"""
This module contains classes and utility functions to deal with users
that can book the microscope and can start a session.
"""

import json
import requests



class BookingManager():
    """ Helper class to interact with the booking system.
    """
    BASE_URL = 'http://cryoem-sverige.bookedscheduler.com/Web/Services/index.php/'

    def getUrl(self, suffix):
        return self.BASE_URL + suffix

    def login(self, userJson):
        """ Login the given user.
        Params:
            userJson: input json dict with the username and password.
        Returns:
            A dict with headers required for next operations.
        """
        userToken = getattr(self, 'userToken', None)

        if userToken is not None:
            return userToken

        url = self.getUrl('Authentication/Authenticate')
        response = requests.post(url, data=json.dumps(userJson))

        if response.status_code != 200:
            print("Error", response.status_code)
            self.userToken = None
        else:
            rJson = response.json()
            # Return headers needed for any further operation
            self.userToken = {'userId': rJson['userId'],
                              'sessionToken': rJson['sessionToken']
                              }

        return self.userToken

    def getHeaders(self, userToken):
        return {'X-Booked-UserId': userToken['userId'],
                'X-Booked-SessionToken': userToken['sessionToken']
                }

    def getJsonData(self, headers, suffix):
        """ Retrieve the reservations, given the user credentials in header. """
        url = self.getUrl(suffix)
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print("Error", response.status_code)
            return None
        else:
            rJson = response.json()
            # Return headers needed for any further operation
            return rJson

    def logout(self, userToken):
        url = self.getUrl('Authentication/SignOut')
        response = requests.post(url, data=json.dumps(userToken))
        if response.status_code != 200:
            print("Error", response.status_code)
        else:
            print("Session closed.")
            self.userToken = None

    def isUserLogged(self):
        return getattr(self, 'userToken', None) is not None

    def fetchJsonFromUrl(self, userJsonFileName, suffix):
        """ Retrieve data from a given url suffix from the booking
        system using the provided user credentials.
        """
        with open(userJsonFileName) as userFile:
            userJson = json.load(userFile)
            # userToken should be a dict containing
            # 'userId' and 'sessionToken' keys
            userToken = self.login(userJson)
            headers = self.getHeaders(userToken)
            jsonData = self.getJsonData(headers, suffix)
            self.logout(userToken)
            return jsonData

        return None

    def fetchReservationsJson(self, userJsonFileName):
        """ Retrieve the reservations from the booking system using the
        credentials of the given user.
         (in a json file {"username": "pp", "password": "kk"} )
        """
        return self.fetchJsonFromUrl(userJsonFileName, 'Reservations/')

    def fetchUsersJson(self, userJsonFileName):
        """ Retrieve the users list from the booking system using the
            credentials of the given user.
            (in a json file {"username": "pp", "password": "kk"} )
        """
        return self.fetchJsonFromUrl(userJsonFileName, 'Users/')
