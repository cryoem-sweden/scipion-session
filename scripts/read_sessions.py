
from model.session import SessionManager
from config import *


dataFn = getDataFile(SESSIONS_FILE)

sMan = SessionManager(dataFn)

sessionsSet = sMan.getSessions()
sessionsSet.enableAppend()
sessions = [s.clone() for s in sessionsSet]


for session in sessions:
    session.printAll()
    session.microscopeSettings.set({"a": 1})
    sessionsSet.update(session)

sessionsSet.write()
