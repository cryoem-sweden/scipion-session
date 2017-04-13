
import json

from pyworkflow.object import String, OrderedObject
import pyworkflow.utils as pwutils


class UString(String):
    def _convertValue(self, value):
        try:
            v = unicode(value)
        except Exception, ex:
            print value, type(value)
            raise

        return v


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
            setattr(self, key, UString(kwargs.get(key, '')))

        for key in self.ATTR_RAW:
            setattr(self, key, kwargs.get(key, None))