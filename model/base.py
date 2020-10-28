
import json
import csv

from pyworkflow.object import String, OrderedObject
import pyworkflow.utils as pwutils


class UString(String):
    def _convertValue(self, value):
        try:
            if isinstance(value, unicode):
                v = value
            elif isinstance(value, str):
                v = unicode(value, encoding='utf-8', errors='ignore')
            else:
                v = str(value)
        except Exception as ex:
            print(value, type(value))
            raise

        return v

    def __str__(self):
        """String representation of the scalar value"""
        return self._objValue


class JsonDict(UString):
    """ Very simple string value for encoding dict as json.
    Only should be used though set/get methods.
    """
    def _convertValue(self, value):
        if isinstance(value, dict):
            v = json.dumps(value)
        else:
            v = UString._convertValue(self, value)

        return v

    def get(self):
        if self._objValue is not None:
            return json.loads(self._objValue)

        return None


class DataObject(OrderedObject):
    """ Class to simply store string attributes passed
    as key=value pairs in the constructor.
    """
    # List of attributes that will be set as UString
    ATTR_STR = []
    ATTR_RAW = []

    def __init__(self, **kwargs):
        OrderedObject.__init__(self)
        # Set automatically a number of string properties

        for key in self.ATTR_STR:
            try:
                setattr(self, key, UString(kwargs.get(key, '')))
            except Exception as ex:
                print("Error trying to set value for '%s' " % key)

        for key in self.ATTR_RAW:
            setattr(self, key, kwargs.get(key, None))


class Person(DataObject):
    """ Simple class to hold name and email values. """
    ATTR_STR = ['email', 'name']

    def setData(self, email, name):
        self.email.set(email)
        self.name.set(name)

    def getName(self):
        return self.name.get()

    def getEmail(self):
        return self.email.get()


def parseCsv(csvFilename, skipFirst=True):

    with open(csvFilename) as dataFile:
        dataReader = csv.reader(dataFile)

        i = 0
        for row in dataReader:
            if row:  # Skip empty lines
                if i > 0 or not skipFirst:
                    yield row
                i += 1
