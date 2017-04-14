
from model.reservations import loadReservations

reservations = loadReservations()

for u in reservations:
    if u.isToday():
        u.printAll()

