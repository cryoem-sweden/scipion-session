
from model.session import SessionManager
from config import *


dataFn = getDataFile(SESSIONS_FILE)

sMan = SessionManager(dataFn)

for session in sMan.getSessions():
    session.printAll()