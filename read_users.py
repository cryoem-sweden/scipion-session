
from model.users import loadUsers

dataFn = 'data/users.csv'

users = loadUsers(dataFn)

for u in users:
    u.printAll()

