
import sys

from model.reservation import loadReservationsFromCsv


if __name__ == "__main__":

    n = len(sys.argv)

    csvFile = sys.argv[1]
    numberOfReservations = int(sys.argv[2]) if n > 2 else 10

    reservations = loadReservationsFromCsv(csvFile)

    print "Reservations: ", len(reservations)

    for r in reservations[:numberOfReservations]:
        r.printAll()
        print "    Days: ", r.getTotalDays()


