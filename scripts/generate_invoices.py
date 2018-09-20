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
from model.reservation import loadReservationsFromCsv


DATA = os.path.join(ROOT, 'data')

def getDataFile(*args):
    return os.path.join(DATA, *args)


TITAN = 'Titan Krios'
TALOS = 'Talos Arctica'

MICROSCOPES = [TITAN, TALOS]


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
                             '</br>Total: %d sessions / %d days'
                             % (fromDate.year, fromDate.month, fromDate.day,
                                toDate.year, toDate.month, toDate.day,
                                len(infoDict), statsDict['days']))
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
        f.write("# Total: %d sessions / %d days \n"
                % (len(infoDict), statsDict['days']))
        f.write("# Generated: %s \n" % now)

        first = infoDict.values()[0]

        f.write("\n%s\n" % " , ".join(k for k in first.keys()))

        for d in infoDict.values():
            f.write(" , ".join(escape(v) for v in d.values()) + '\n')

        print("Written: %s" % csvFn)
    else:
        print("Error opening: %s" % csvFn)


def getInfoFromOrders(reservations):
    """ Create the info dictionary that will be used the invoices based
    on the reservations that are national facility projects (i.e. orders)
    """
    rDict = {}

    for r in reservations:
        cemCode = r.getCemCode()
        if r.resource in MICROSCOPES:
            if r.isNationalFacility():
                if cemCode not in rDict:
                    rDict[cemCode] = []
                rDict[cemCode].append(r)
            else:
                if 'cem0' in r.title.get().lower():
                    print "Not CEM: ", r.title.get()

    infoDict = OrderedDict()
    statsDict = {'days': 0}

    for cemCode in sorted(rDict.keys()):
        # print "-" * 20
        # print "CEM: ", cemCode
        o = data.getOrder(cemCode)

        if o is None:
            print(">>> ERROR: Order not found for this CEM code: %s"
                  % pwutils.redStr(cemCode))
            for r in rDict[cemCode]:
                print("    Resource: %s (%s - %s)"
                      % (r.username, r.beginDate(), r.endDate()))
                print("    User: %s" % r.username)

            continue

        #print " title: ", o.getTitle()
        #print " order.id: ", o.getId()

        o.fields = data.getOrderDetails(cemCode)['fields']

        info = OrderedDict()
        info['Project Code'] = cemCode.upper()
        info['Project Title'] = o.getTitle()
        info['Hours allocated'] = 0
        info['Dates'] = ''
        info['PI'] = '%s </br></br> %s' % (o.getPi(), o.getPiEmail())
        info['Amount (SEK)'] = 0
        info['Invoice Address'] = o.getInvoiceAddress()
        info['Invoice Reference'] = o.getInvoiceReference()
        infoDict[cemCode] = info
        dates = []
        days = 0

        for r in rDict[cemCode]:
            d = r.beginDate()
            duration = max(1, r.getTotalDays())
            days += duration
            dates.append('%04d-%02d-%02d (%s) (%d)' %
                         (d.year, d.month, d.day,
                          r.resource, duration))
        info['Count (days)'] = days
        info['Dates'] = '</br>'.join(dates)
        info['Hours allocated'] = days * 24
        info['Amount (SEK)'] = days * 5000
        statsDict['days'] += days

    return infoDict, statsDict


def getInfoFromInternal(reservations, sessions, group):
    """

    :param reservations: We need this until all info is stored in sessions
    :param sessions: Stored sessions
    :param group: Should be either 'dbb' or 'sll'
    :return:
    """
    infoDict = OrderedDict()
    statsDict = {'days': 0}
    i = 0

    for s in sessions:
        sessionCode = s.sessionCode.get()
        if sessionCode.startswith(group):
            r = s.reservation
            if group == 'fac':
                t = r.title.get().lower()
                if ('cryocycle' in t or 'cryo cycle' in t or 'cryo-cycle' in t or
                    'downtime' in t or 'down' in t or 'fei' in t or
                    'maintenance' in t):
                    continue

            # print "-" * 20
            # print "Session code: ", sessionCode
            # print "date: ", s.reservation.beginDate()

            info = OrderedDict()
            i += 1

            info['Entry'] = i
            info['Project Code'] = sessionCode
            info['User'] = '%s </br></br> %s' % (s.user.name, s.user.email)
            info['Dates'] = '%s (%s)' % (r.beginDate(),
                                         s.microscope)
            info['PI'] = '%s </br></br> %s' % (s.pi.name, s.pi.email)
            days = r.getTotalDays()
            cost = 5000 * days
            statsDict['days'] += days
            info['Amount (SEK)'] = cost
            info['Duration (days)'] = days
            invoice = s.invoice.get()
            if invoice:
                iAddr, iRef = invoice['address'], invoice['reference']
            else:
                iAddr, iRef = '', ''
            info['Invoice Address'] = iAddr
            info['Invoice Reference'] = iRef
            infoDict[sessionCode+str(i)] = info
            if group == 'fac':
                info['Title'] = r.title.get()

    return infoDict, statsDict

def getSessionsFromReservations(data):
    """ Update the session with information from the reservations...
    """
    reservations = data.getReservations()
    reservations.sort(key=lambda r: r.beginDate())

    sessions = []

    #for s in sessions:
    #    sessionDict[s.user.email.get()] = s.clone()

    for r in reservations:
        if not r.isNationalFacility() and r.resource in MICROSCOPES:
            u = data.findUserFromReservation(r)
            s = data.createSessionFromUser(u)
            data.setupInternalSession(s, u)
            s.isNational.set(False)
            s.microscope.set(r.resource)
            s.sessionCode.set(u.getGroup())
            s.reservation = r
            sessions.append(s)

    return sessions


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

    data = Data(dataFolder=DATA, fromDate=fromDate, toDate=toDate)

    if '--csv' in sys.argv:
        csvIndex = sys.argv.index('--csv')
        csvFile = sys.argv[csvIndex + 1]
        reservations = loadReservationsFromCsv(csvFile)
    else:
        reservations = data.getReservations()

    if reservations:
        allDict = OrderedDict()
        allStats = {}

        # Generate invoices for national facility projects
        allDict[NATIONAL], allStats[NATIONAL] = getInfoFromOrders(reservations)

        sessions = data.getSessions()
        sessions = getSessionsFromReservations(data)

        # Writing FAC booking reservations into a CSV file
        # fn = getDataFile('fac-session.csv')
        # f = codecs.open(fn, "w", "utf-8")
        #
        # print "Writing Facility sessions to: ", fn
        # for s in sessions:
        #     sessionCode = s.sessionCode.get()
        #     if sessionCode.startswith('fac'):
        #         d = s.reservation.beginDate()
        #         print >> f,  "%s\t,%s,\t%s,\t%s,\t%s" % (s.reservation.reference.get(),
        #                                             s.reservation.beginDate(),
        #                                s.reservation.username.get(),
        #                                s.microscope.get(),
        #                                s.reservation.title.get())
        #
        # f.close()
        # sys.exit(1)

        # Reading annotations of Non-FAC bookings
        annotations = {}
        # fn = getDataFile('fac-session-annotated.csv')
        # f = codecs.open(fn, "r", "utf-8")
        # for line in f:
        #     if line.strip():
        #         parts = line.strip().split(',')
        #         annotations[parts[0]] = parts[-1]

        extraCount = {}
        MAINTENANCE = 'MAINTENANCE'
        DOWNTIME = 'DOWNTIME'
        for group in [FAC, DBB, SLL, DOWNTIME, MAINTENANCE]:
            extraCount[group] = 0

        # for s in sessions:
        #     sessionCode = s.sessionCode.get()
        #     title = s.reservation.title.get().lower()
        #     if sessionCode.startswith('fac'):
        #         ref = s.reservation.reference.get()
        #         if ref in annotations:
        #             a = annotations[ref].lower()
        #             if 'sll' in a:
        #                 extraCount[SLL] += 1
        #             elif 'dbb' in a:
        #                 extraCount[DBB] += 1
        #             elif ('fei' in a or 'cryo cycle' in a or 'maintenance' in title or
        #                   'cryo-cycle' in title or 'cryo cycle' in title):
        #                 extraCount[MAINTENANCE] += 1
        #             elif ('downtime' in a or 'downtime' in title or 'down' in title):
        #                 extraCount[DOWNTIME] += 1
        #             else:
        #                 extraCount[FAC] += 1 # just to decrement later and keep the same value
        #             extraCount[FAC] -= 1

        # Generate invoices for dbb projects
        allDict[DBB], allStats[DBB] = getInfoFromInternal(reservations, sessions, group='dbb')

        # Generate invoices for dbb projects
        allDict[SLL], allStats[SLL] = getInfoFromInternal(reservations, sessions, group='sll')

        # Generate invoices for fac projects
        allDict[FAC], allStats[FAC] = getInfoFromInternal(reservations, sessions, group='fac')

        if not stats:
            for name, statDict in allDict.iteritems():
                generateInvoice(statDict, name, allStats[name])
                generateInvoiceCsv(statDict, name, allStats[name])
        else:
            # ======= Total distribution of projects ==================
            total = 0
            for name, statDict in allStats.iteritems():
                n = statDict['days']
                # if name == NATIONAL:
                #     print "Number of National Projects: ", len(statDict)
                #     n = 0
                #     for info in statDict.values():
                #         n += info['days']
                # else:
                #     n = len(statDict)
                if name in extraCount:
                    n += extraCount[name]
                print "%s:\t%s:\tdays: %s" % (name, len(allDict[name]), n)
                total += n

            for name in [DOWNTIME, MAINTENANCE]:
                n = extraCount[name]
                print "%s:\t%s" % (name, n)
                total += n
            print "Total:\t%s" % total


            # ======= Geographical distribution of National projects =======

            locations = [('stockholm', ['stockholm', 'solna', 'karolinska']),
                         ('uppsala', ['uppsala']),
                         ('gothenburg', ['gothenburg', u'göteborg']),
                         ('linkoping', [u'linköping']),
                         ('lund', ['lund'])
                         ]

            def _getLocation(address):
                addressLower = address.lower()
                for locName, locAliases in locations:
                    for loc in locAliases:
                        if loc in addressLower:
                            return locName
                return None

            locationCount = OrderedDict()
            for loc, _ in locations:
                locationCount[loc] = 0

            # Geographical distribution of national projects
            for info in allDict[NATIONAL].values():
                loc = _getLocation(info['Referens'])
                if loc:
                    locationCount[loc] += 1
                else:
                    print "Unknown location: ", info['Referens']
                    #sys.exit(1)

            print locationCount

            # ========== Check wrong CEM bookings =============
            for info in allDict[FAC].values():
                codeLower = info['Project Code']

    else:
        print "No reservation found. "
