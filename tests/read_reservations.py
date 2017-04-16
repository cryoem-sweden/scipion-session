
from model.reservation import loadReservations

reservations = loadReservations()

for u in reservations:
    if u.isToday():
        u.printAll()

