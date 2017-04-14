
from model.user import loadUsers

dataFn = 'data/users.csv'

users = loadUsers()

for u in users:
    u.printAll()

