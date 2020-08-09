#!/usr/bin/env python
# -*- coding: utf-8 -*-
# **************************************************************************
# *
# * Authors:     J.M. De la Rosa Trevin (delarosatrevin@scilifelab.se) [1]
# *
# * [1] SciLifeLab, Stockholm University
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'delarosatrevin@scilifelab.se'
# *
# **************************************************************************

import os
import sys
import codecs

import datetime as dt
from collections import OrderedDict
import pyworkflow.utils as pwutils


# Assume the data folder is in the same place as this script
ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

sys.path.append(ROOT)

# Local imports after ROOT has been added to the path
from model.data import Data
from model.reservation import loadReservationsFromCsv, Reservation
from model.session import Session
from model.base import Person

from config import *


def parseDate(dateStr):
    """ Get date from YYYY/MM/DD string """
    year, month, day = dateStr.split('/')
    return dt.datetime(year=int(year), month=int(month), day=int(day))


def usage(error):
    print """
    ERROR: %s

    Usage: generate_invoices.py FROM_DATE TO_DATE
        Dates must be in the following format: YYYY/MM/DD
    """ % error
    sys.exit(1)


def openFile(fn):
    import codecs
    return codecs.open(fn, "w", "utf-8-sig")


def generateInvoice(infoDict, invoiceType, statsDict):
    htmlTemplate = open('report/invoices.html.template')
    suffix = invoiceType.lower().replace(' ', '_')
    htmlFn = os.path.join('build', 'invoices_%s.html' % suffix)
    outputHtml = openFile(htmlFn)
    now = dt.datetime.now()

    def writeEntry(d):
        outputHtml.write("<table>\n")
        for key, value in d.iteritems():
            try:
                print >> outputHtml, "<tr><th>", key
                print >> outputHtml, "</th><td>", value
                print >> outputHtml, "</td></tr>"
            except Exception, ex:
                print "Error:", value

        outputHtml.write("</table>\n")
        print >> outputHtml, "</br></br>"

    def writeAllEntries():
        for d in infoDict.values():
            writeEntry(d)

    invoiceTitle = 'Invoices: %s' % invoiceType

    for line in htmlTemplate:
        if '<!--- TITLE --->' in line:
            outputHtml.write("<title> Swedish National Cryo-EM Facility - "
                             "%s </title>" % invoiceTitle)
        elif '<!--- INVOICE-TYPE --->' in line:
            outputHtml.write(invoiceTitle)
        elif '<!--- INVOICES --->' in line:
            writeAllEntries()
        elif '<!--- PERIOD --->' in line:
            outputHtml.write('from %04d-%02d-%02d to %04d-%02d-%02d  '
                             '</br>Total: %d sessions / %d days / %d SEK'
                             % (fromDate.year, fromDate.month, fromDate.day,
                                toDate.year, toDate.month, toDate.day,
                                statsDict['sessions'], statsDict['days'], statsDict['cost']))
        elif '<!--- TIMESTAMP --->' in line:
            outputHtml.write('%s' % now)
        else:
            outputHtml.write(line)

    htmlTemplate.close()
    outputHtml.close()

    # Convert to pdf, assuming that wkhtmltopdf is installed in the system

    pdfFn = htmlFn.replace('.html', '_%04d%02d%02d.pdf'
                           % (now.year, now.month, now.day))
    cmd = 'wkhtmltopdf --zoom 3 %s %s' % (htmlFn, pdfFn)
    print cmd
    os.system(cmd)


def generateInvoiceCsv(infoDict, invoiceType, statsDict):
    now = dt.datetime.now()
    suffix = invoiceType.lower().replace(' ', '_')
    csvFn = os.path.join('build', 'invoices_%s_%04d%02d%02d.csv'
                         % (suffix, now.year, now.month, now.day))

    def escape(s):
        return '"%s"' % unicode(s).replace('\n', ' ').replace('\r', ' ').replace('</br>', '')

    f = openFile(csvFn)

    if f:
        f.write("# Swedish National Cryo-EM Facility - Invoices: %s\n"
                % invoiceType)
        f.write("# from %04d-%02d-%02d to %04d-%02d-%02d  \n"
                % (fromDate.year, fromDate.month, fromDate.day,
                   toDate.year, toDate.month, toDate.day))
        f.write("# Total: %(sessions)d sessions / %(days)d days / %(cost)d SEK\n"
                % statsDict)
        f.write("# Generated: %s \n" % now)

        infoDictCopy = OrderedDict(infoDict)
        for d in infoDict.values():
            del d['Sessions']

        first = infoDictCopy.values()[0]

        import csv
        with open(csvFn, 'w') as f:
            writer = csv.writer(f, dialect=csv.excel)
            writer.writerow(list(first.keys()))

            for d in infoDictCopy.values():
                writer.writerow([unicode(s).encode('utf-8') for s in d.values()])

        print("Written: %s" % csvFn)
    else:
        print("Error opening: %s" % csvFn)


def getInfoFromNationals(reservations, sessions):
    """ Create the info dictionary that will be used the invoices based
    on the reservations that are national facility projects (i.e. orders)
    """
    cemDict = OrderedDict()
    infoDict = OrderedDict()
    statsDict = {'days': 0, 'sessions': 0, 'cost': 0}

    for r in reservations:
        if not r.isNationalFacility():
            continue
        cemCode = r.getCemCode()
        if not cemCode in cemDict:
            cemDict[cemCode] = []
        cemDict[cemCode].append(r)

    for cemCode, cemReservations in cemDict.iteritems():
        o = data.getOrder(cemCode)
        if o is None:
            print("Invalid order code: %s, got None...SKIPPING" % cemCode)
            continue

        o.fields = data.getOrderDetails(cemCode)['fields']

        cemSessions = []
        days = 0
        # for r in cemReservations:
        #     days += r.getTotalDays()
        #     for s in sessions:
        #         if s.getCem() == cemCode and r.isActiveOnDay(s.date.date()):
        #             s.reservation = r
        #             cemSessions.append(s)
        #
        # sessionsDict = OrderedDict()  # used to remove duplicated sessions
        # for s in cemSessions:
        #     sessionsDict[(s.date.date(), s.getMicroscope())] = s

        # sessionsStr = "<ul>"
        # for (date, microscope), s in sessionsDict.iteritems():
        #     formatStr = '<li>%s  %s %s <ul><li>PI: %s, User: %s</li></ul></li>'
        #     sessionsStr += (formatStr %
        #                     (s.date.date(), s.getId(), s.getMicroscope(),
        #                      s.pi.getName(), s.user.getName()))
        # sessionsStr += "</ul>"
        totalSessions = 0
        sessionsStr = ""
        piDict = OrderedDict()

        for microscope1 in MICROSCOPES:
            sessionsStr += "<h4>%s</h4>" % microscope1
            for r in cemReservations:
                if r.resource != microscope1:
                    continue

                sessionsStr += ("<h6>%s %s - %s (%s)</h6><ul>"
                                % (r.title, r.beginDate().date(),
                                   r.endDate().date(), r.getTotalDays()))
                days += r.getTotalDays()
                r.sessions = []

                for s in sessions:
                    s.duration = 0
                    if s.getCem() == cemCode and s.getMicroscope() == microscope1 and r.isActiveOnDay(s.date.date()):
                        s.reservation = r
                        if r.sessions:
                            prevSession = r.sessions[-1]
                            prevSession.duration = (s.date.date() - prevSession.date.date()).days
                        r.sessions.append(s)
                        totalSessions += 1

                # Compute duration for last session inside this reservation
                if r.sessions:
                    prevSession = r.sessions[-1]
                    prevSession.duration = (r.endDate().date() - prevSession.date.date()).days + 1

                for s in r.sessions:
                    formatStr = '<li>%s %s  (%d) <ul><li>PI: %s, User: %s</li></ul></li>'
                    piName = s.pi.getName()
                    sessionsStr += (formatStr % (s.date.date(), s.getId(), s.duration,
                                                 piName, s.user.getName()))
                    if piName not in piDict:
                        piDict[piName] = 0
                    piDict[piName] += s.duration

                sessionsStr += "</ul>"

            # for (date, microscope2), s in sessionsDict.items():
            #     if microscope1 == microscope2:
            #         formatStr = '<li>%s %s  (%d) <ul><li>PI: %s, User: %s</li></ul></li>'
            #         sessionsStr += (formatStr % (s.date.date(), s.getId(), s.reservation.getTotalDays(),
            #                                      s.pi.getName(), s.user.getName()))
            # sessionsStr += "</ul>"
        # sessionsStr += "</ul>"
        sessionsStr += "<h4>Summary</h4><ul>"
        for piName, total in piDict.items():
            sessionsStr += "<li>%s   %s</li>" % (piName, total)
        sessionsStr += "</ul>"

        info = OrderedDict()
        info['Project Code'] = cemCode.upper()
        #info['Project Title'] = o.getTitle()
        info['Sessions'] = sessionsStr
        info['Count (days)'] = days
        info['Hours allocated'] = days * 24
        cost = days * 5000
        info['Amount (SEK)'] = cost
        info['PI'] = '%s </br></br> %s' % (o.getPi(), o.getPiEmail())
        info['Invoice Address'] = o.getInvoiceAddress()
        info['Invoice Reference'] = o.getInvoiceReference()
        info[''] = '<footer></footer>'

        statsDict['days'] += days
        statsDict['sessions'] += totalSessions
        statsDict['cost'] += cost
        infoDict[cemCode] = info

    return infoDict, statsDict


def getInfoFromInternal(reservations, sessions, group):
    """
    :param reservations: We need this until all info is stored in sessions
    :param sessions: Stored sessions
    :param group: Should be either 'dbb' or 'sll'
    :return:
    """
    infoDict = OrderedDict()
    statsDict = {'days': 0, 'sessions': 0, 'cost': 0}
    i = 0

    rDict = OrderedDict()

    def _matchGroup(u):
        """ Check correct group. """
        if isinstance(group, list):
            return u.getGroup() in group
        else:
            return u.getGroup() == group

    # Group reservations by PI
    for r in reservations:
        u = r.user
        if not _matchGroup(u) or r.isDowntime() or not r.resource.get() in MICROSCOPES:
            continue

        if u.isStaff():
            piKey = (u.getEmail(), u.getFullName())
            piLabel = 'User'
        else:
            piEmail = (u.getEmail() if u.isPi() else u.getPiEmail()) or 'UNKNOWN PI'
            piName = (u.getFullName() if u.isPi() else u.getPiName()) or 'UNKNOWN PI'
            piKey = (piEmail, piName)
            piLabel = 'PI'

        if piKey not in rDict:
            rDict[piKey] = []

        rDict[piKey].append(r)

    for piKey, reservations in rDict.iteritems():
        u = r.user
        days = 0
        sessionsStr = "<ul>"
        for microscope in MICROSCOPES:
            sessionsStr += "<li>%s<ul>" % microscope
            for r in reservations:
                if microscope == r.resource.get():
                    formatStr = '<li>%s (%d) %s</li>'
                    sessionsStr += (formatStr % (r.beginDate().date(),
                                                 r.getTotalDays(),
                                                 r.user.getFullName()))
                    days += r.getTotalDays()
            sessionsStr += "</ul>"
        sessionsStr += "</ul>"

        info = OrderedDict()
        i += 1

        info['Entry'] = i
        info[piLabel] = piKey[1]
        cost = 5000 * days

        info['Sessions'] = sessionsStr
        info['Duration (days)'] = days
        info['Hours allocated'] = days * 24
        info['Amount (SEK)'] = cost
        info[''] = '<footer></footer>'

        statsDict['days'] += days
        statsDict['sessions'] += len(reservations)
        statsDict['cost'] += cost
        # TODO: Get the PI's reference from the portalen
        # iAddr, iRef = '', ''
        # info['Invoice Address'] = iAddr
        # info['Invoice Reference'] = iRef

        infoDict[r.user.getGroup()+str(i)] = info

    return infoDict, statsDict


NATIONAL = "National Projects"
DBB = "DBB"
SLL = "SciLifeLab"
FAC = "Facility"


if __name__ == "__main__":
    n = len(sys.argv)

    if n < 2:
        usage("Incorrect number of arguments")

    stats = '--stats' in sys.argv

    now = dt.datetime.now()
    fromDate = parseDate(sys.argv[1])
    toDate = parseDate(sys.argv[2])

    data = Data(dataFolder=getDataFile(), fromDate=fromDate, toDate=toDate)

    if '--csv' in sys.argv:
        csvIndex = sys.argv.index('--csv')
        csvFile = sys.argv[csvIndex + 1]
        reservations = loadReservationsFromCsv(csvFile)
    else:
        reservations = data.getReservations()

    if reservations:
        allDict = OrderedDict()
        allStats = {}

        sessions = data.getSessions()

        totalCount = {}
        downDict = {'days': 0, 'sessions': 0}
        for r in reservations:
            if r.isDowntime():
                downDict['sessions'] += 1
                downDict['days'] += r.getTotalDays()

        allStats['DOWNTIME'] = downDict

        # Generate invoices for national facility projects
        allDict[NATIONAL], allStats[NATIONAL] = getInfoFromNationals(reservations, sessions)

        # # Generate invoices for dbb projects
        allDict[DBB], allStats[DBB] = getInfoFromInternal(reservations, sessions, group=['dbb', 'sll'])
        #
        # # Generate invoices for fac projects
        allDict[FAC], allStats[FAC] = getInfoFromInternal(reservations, sessions, group='fac')

        if not stats:
            for name, statDict in allDict.iteritems():
                generateInvoice(statDict, name, allStats[name])
                generateInvoiceCsv(statDict, name, allStats[name])
        else:
            # ======= Invoiced PIs =======
            print("Invoiced PIs: ")
            piList = []
            for name, statDict in allDict.iteritems():
                for d in statDict.values():
                    if 'PI' in d:
                        #print(d['PI'])
                        piList.append(d['PI'])
            print("Total PIs: %s" % len(piList))

            # ======= Total distribution of projects ==================
            total = 0
            for name, statDict in allStats.iteritems():
                n = statDict['days']
                if 'sessions' in statDict:
                    count = statDict['sessions']
                else:
                    count = len(allDict[name])

                print "%s:\tsessions: %s:\tdays: %s" % (name, count, n)
                total += n

            print "Total:\t%s" % total


            # ======= Geographical distribution of National projects =======

            locations = [('stockholm', ['stockholm', 'solna', 'karolinska']),
                         ('uppsala', ['uppsala']),
                         ('gothenburg', ['gothenburg', u'göteborg']),
                         ('linkoping', [u'linköping']),
                         ('lund', ['lund']),
                         ('umea', ['umea', u'umeå'])
                         ]

            def _getLocation(address):
                try:
                    addressLower = address.lower()
                    for locName, locAliases in locations:
                        for loc in locAliases:
                            if loc in addressLower:
                                return locName
                except:
                    pass
                return None

            locationCount = OrderedDict()
            for loc, _ in locations:
                locationCount[loc] = 0

            # Geographical distribution of national projects
            for info in allDict[NATIONAL].values():
                addressValue = info['Invoice Address']
                loc = _getLocation(addressValue)
                if loc:
                    locationCount[loc] += info['Count (days)']
                else:
                    print("Unknown location: %s" % addressValue)
                    #sys.exit(1)

            print locationCount

            # ========== Check wrong CEM bookings =============
            # for info in allDict[FAC].values():
            #     pwutils.prettyDict(info)
                # codeLower = info['Project Code']

    else:
        print "No reservation found. "
