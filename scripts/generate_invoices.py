
import sys
import os
import datetime as dt
import argparse
from collections import OrderedDict

from model.data import Data

TITAN = 'Titan Krios'
TALOS = 'Talos Arctica'

MICROSCOPES = [TITAN, TALOS]


def parseDate(dateStr):
    """ Get date from YYYY/MM/DD string """
    year, month, day = dateStr.split('/')
    return dt.datetime(year=int(year), month=int(month), day=int(day))


if __name__ == "__main__":

    # Assume the data folder is in the same place as this script
    dataFolder = os.path.join(os.path.dirname(__file__), '..', 'data')

    data = Data(dataFolder=dataFolder)
    now = dt.datetime.now()
    fromDate = dt.datetime(year=2017, month=2, day=1)
    toDate = dt.datetime(year=2017, month=4, day=30)

    def inRange(r):
        """ True the reservation date is between fromDate and toDate """
        return r.beginDate() >= fromDate and r.endDate() <= toDate

    reservations = data.findReservations(inRange)

    if reservations:
        rDict = {}
        for r in reservations:
            cemCode = r.getCemCode()
            if r.isNationalFacility() and r.resource in MICROSCOPES:
                if cemCode not in rDict:
                    rDict[cemCode] = []
                rDict[cemCode].append(r)

        infoDict = OrderedDict()

        for cemCode in sorted(rDict.keys()):
            print "-" * 20
            print "CEM: ", cemCode
            o = data.getOrder(cemCode)
            print " title: ", o.getTitle()
            print " order.id: ", o.getId()

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


        htmlTemplate = open('report/invoices.html.template')
        import codecs

        htmlFn = os.path.join('build', 'invoices.html')
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

        for line in htmlTemplate:
            if '<!--- INVOICES --->' in line:
                writeAllEntries()
            elif '<!--- PERIOD --->' in line:
                outputHtml.write('%04d/%02d/%02d - %04d/%02d/%02d'
                                 % (fromDate.year, fromDate.month, fromDate.day,
                                    toDate.year, toDate.month, toDate.day))
            else:
                outputHtml.write(line)

        htmlTemplate.close()
        outputHtml.close()

        # Convert to pdf, assuming that wkhtmltopdf is installed in the system

        pdfFn = htmlFn.replace('.html', '_%04d%02d%02d-%02d%02d.pdf'
                               % (now.year, now.month, now.day,
                                  now.hour, now.minute))
        cmd = 'wkhtmltopdf --zoom 3 %s %s' % (htmlFn, pdfFn)
        print cmd
        os.system(cmd)

    else:
        print "No reservation found. "
