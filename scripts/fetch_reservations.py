"""

"""

import os
import json
import requests


BASE_URL = 'http://cryoem-sverige.bookedscheduler.com/Web/Services/index.php/'
DEBUG = True


def debug(msg):
    if DEBUG:
        print("DEBUG: ", msg)


def getUrl(suffix):
    return BASE_URL + suffix


def login(userJson):
    """ Login the given user.
    Params:
        userJson: input json dict with the username and password.
    Returns:
        A dict with headers required for next operations.
    """
    url = getUrl('Authentication/Authenticate')
    response = requests.post(url, data=json.dumps(userJson))

    if response.status_code != 200:
        print("Error", response.status_code)
        return None
    else:
        rJson = response.json()
        debug("login: %s" % rJson)
        # Return headers needed for any further operation
        return {'userId': rJson['userId'],
                'sessionToken': rJson['sessionToken']
                }


def getHeaders(userToken):
    return {'X-Booked-UserId': userToken['userId'],
            'X-Booked-SessionToken': userToken['sessionToken']
            }


def getReservations(headers):
    """ Retrieve the reservations, given the user credentials in header. """
    url = getUrl('Reservations/')
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Error", response.status_code)
        return None
    else:
        rJson = response.json()
        debug(response.text)
        # Return headers needed for any further operation
        return rJson


def logout(userToken):
    url = getUrl('Authentication/SignOut')
    response = requests.post(url, data=json.dumps(userToken))
    if response.status_code != 200:
        print("Error", response.status_code)
    else:
        print("Session closed.")


if __name__ == "__main__":
    # Assume the data folder is in the same place as this script
    dataFolder = os.path.join(os.path.dirname(__file__), '../data')
    # Load username and password for booked system
    userJson = json.load(open('%s/booked-user.json' % dataFolder))
    # userToken should be a dict containing 'userId' and 'sessionToken' keys
    userToken = login(userJson)
    headers = getHeaders(userToken)
    getReservations(headers)
    logout(userToken)
