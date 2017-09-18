#!/usr/bin/env python
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

import datetime as dt
from collections import OrderedDict


# Assume the data folder is in the same place as this script
ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

sys.path.append(ROOT)

# Local imports after ROOT has been added to the path
from model.data import Data


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


def generateInvoice(infoDict, invoiceType):
    htmlTemplate = open('report/invoices.html.template')
    import codecs

    suffix = invoiceType.lower().replace(' ', '_')
    htmlFn = os.path.join('build', 'invoices_%s.html' % suffix)
    outputHtml = codecs.open(htmlFn, "w", "utf-8-sig")

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
            outputHtml.write('from %04d-%02d-%02d to %04d-%02d-%02d'
                             % (fromDate.year, fromDate.month, fromDate.day,
                                toDate.year, toDate.month, toDate.day))
        elif '<!--- TIMESTAMP --->' in line:
            outputHtml.write('%s' % dt.datetime.now())
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


def getInfoFromOrders(reservations):
    """ Create the info dictionary that will be used the invoices based
    on the reservations that are national facility projects (i.e. orders)
    """
    rDict = {}

    for r in reservations:
        cemCode = r.getCemCode()
        print "cemCode: ",
        if r.isNationalFacility() and r.resource in MICROSCOPES:
            if cemCode not in rDict:
                rDict[cemCode] = []
            rDict[cemCode].append(r)

    infoDict = OrderedDict()

    for cemCode in sorted(rDict.keys()):
        print "-" * 20
        print "CEM: ", cemCode
        o = data.getOrder(cemCode)

        if o is None:
            print "ERROR: Order not found for this CEM code. "
            continue

        print " title: ", o.getTitle()
        print " order.id: ", o.getId()

        o.fields = data.getOrderDetails(cemCode)['fields']

        info = OrderedDict()
        info['Project Code'] = cemCode.upper()
        info['Project Title'] = o.getTitle()
        info['Hours allocated'] = 0
        info['Dates'] = ''
        info['PI'] = '%s </br></br> %s' % (o.getPi(), o.getPiEmail())
        info['Ammount'] = 0
        info['Referens'] = o.getInvoiceAddress()
        infoDict[cemCode] = info
        dates = []
        days = 0
        for r in rDict[cemCode]:
            d = r.beginDate()
            duration = max(1, r.getDuration().days)
            days += duration
            dates.append('%04d-%02d-%02d (%s) (%d)' %
                         (d.year, d.month, d.day,
                          r.resource, duration))

        info['Dates'] = '</br>'.join(dates)
        info['Hours allocated'] = days * 24
        info['Ammount'] = days * 5000

    return infoDict


def getInfoFromInternal(reservations, sessions, group):
    """

    :param reservations: We need this until all info is stored in sessions
    :param sessions: Stored sessions
    :param group: Should be either 'dbb' or 'sll'
    :return:
    """
    infoDict = OrderedDict()
    i = 0

    for s in sessions:
        sessionCode = s.sessionCode.get()
        if sessionCode.startswith(group):
            print "-" * 20
            print "Session code: ", sessionCode
            print "date: ", s.reservation.beginDate()

            info = OrderedDict()
            i += 1
            info['Entry'] = i
            info['Project Code'] = sessionCode
            info['User'] = '%s </br></br> %s' % (s.user.name, s.user.email)
            info['Dates'] = '%s (%s)' % (s.reservation.beginDate(),
                                         s.microscope)
            info['PI'] = '%s </br></br> %s' % (s.pi.name, s.pi.email)
            info['Ammount'] = 500
            info['Duration'] = s.reservation.getDuration()

            invoice = s.invoice.get()
            if invoice:
                invoiceAddr = invoice['address']
            else:
                invoiceAddr = ''

            info['Invoice Address'] = invoiceAddr

            infoDict[sessionCode+str(i)] = info
            dates = []
            days = 0
            # for r in rDict[cemCode]:
            #     d = r.beginDate()
            #     duration = max(1, r.getDuration().days)
            #     days += duration
            #     dates.append('%04d-%02d-%02d (%s) (%d)' %
            #                  (d.year, d.month, d.day,
            #                   r.resource, duration))
            #
            # info['Dates'] = '</br>'.join(dates)
            # info['Hours allocated'] = days * 24
            # info['Ammount'] = days * 5000

    return infoDict

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



if __name__ == "__main__":
    n = len(sys.argv)

    if n < 2 or n > 3:
        usage("Incorrect number of arguments")

    now = dt.datetime.now()
    fromDate = parseDate(sys.argv[1])
    toDate = parseDate(sys.argv[2])

    data = Data(dataFolder=DATA, fromDate=fromDate, toDate=toDate)

    reservations = data.getReservations()

    if reservations:
        # Generate invoices for national facility projects
        infoDict = getInfoFromOrders(reservations)
        generateInvoice(infoDict, invoiceType="National Projects")

        sessions = data.getSessions()
        sessions = getSessionsFromReservations(data)

        # Generate invoices for dbb projects
        infoDict = getInfoFromInternal(reservations, sessions, group='dbb')
        generateInvoice(infoDict, invoiceType="DBB")

        # Generate invoices for dbb projects
        infoDict = getInfoFromInternal(reservations, sessions, group='sll')
        generateInvoice(infoDict, invoiceType="SciLifeLab")

    else:
        print "No reservation found. "
