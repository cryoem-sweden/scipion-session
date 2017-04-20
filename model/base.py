
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
        except Exception, ex:
            print value, type(value)
            raise

        return v

    def __str__(self):
        """String representation of the scalar value"""
        return self._objValue


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
            except Exception, ex:
                print "Error trying to set value for '%s' " % key

        for key in self.ATTR_RAW:
            setattr(self, key, kwargs.get(key, None))


def parseCsv(csvFilename, skipFirst=True):

    with open(csvFilename) as dataFile:
        dataReader = csv.reader(dataFile)

        for i, row in enumerate(dataReader):
            if i > 0 or not skipFirst:
                yield row
