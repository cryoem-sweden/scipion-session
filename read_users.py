
from model.users import loadUsers

dataFn = 'data/users.csv'

users = loadUsers()

for u in users:
    u.printAll()

