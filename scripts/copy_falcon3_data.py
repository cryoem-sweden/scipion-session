#!/usr/bin/env python
"""
This script copy raw movie files from /mnt/krios-falcon3/xxx or /mnt/talos-falcon3/xxx
to the project folder under the name of f3_frames. It will try to infer the xxx project code
and figure out from the there the output folder.
"""
import sys
import os
import re
import time

import pyworkflow.utils as pwutils


def usage(error):
    print """
    ERROR: %s

    Usage: copy_falcon3_data.py FALCON3_EPU_FOLDER [PROJECT_ID]
        FALCON3_EPU_FOLDER: This should be either /mnt/krios-falcon3 or /mnt/talos-falcon3
            If the project code was used in the given folder, it will be parsed from there.

        PROJECT_ID: This parameter is optional and will be inferred from the FALCON3_EPU_FOLDER
            but it will need to be provided if the convention was not followed.
    """ % error
    sys.exit(1)


def system(cmd):
    print cmd
    os.system(cmd)


class ProjCode:
    GROUPS = ['cem', 'fac', 'sll', 'dbb']
    REGEX = re.compile("(%s)(\d+)" % '|'.join(GROUPS))

    def __init__(self, group, number):
        self.group = group
        self.number = int(number)
        self.code = "%s%05d" % (group, self.number)

    def __str__(self):
        return self.code

    @classmethod
    def parse(cls, inputStr):
        """ Try to parse project code from the input
        string. Return None if not possible to parse """
        inputLower = inputStr.lower()

        m = cls.REGEX.search(inputLower)

        if m is not None:
            group = m.groups()[0]
            digits = m.groups()[1]
            if len(digits) != 5:
                print("WARNING: Wrong number of digits for project code in: ",
                      inputStr)
            return ProjCode(group, digits)
        return None


if __name__ == "__main__":
    n = len(sys.argv)

    if n < 2 or n > 3:
        usage("Incorrect number of input parameters")

    dataFolder = sys.argv[1]

    if not os.path.exists(dataFolder):
        usage("Input folder '%s' does not exists" % dataFolder)

    code = ProjCode.parse(dataFolder)

    if code is None:
        if n < 3:
            usage("Could not parse Project Code from input data.\n        "
                  "You need to provide the PROJECT_CODE as second argument")

        codeStr = sys.argv[2]
        code = ProjCode.parse(codeStr)

        if code is None:
            usage("Invalid Project Code provided: %s" % codeStr)

    outputFolder = '/data/staging/%s/%s/f3_frames' % (code.group, str(code))

    print "Output folder: %s" % outputFolder
    pwutils.makePath(outputFolder)

    while True:
        system("rsync -avuP %s/ %s/" % (dataFolder, outputFolder))
        time.sleep(60)

