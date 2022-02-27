from finorch.sessions.cit import CITSession
from finorch.sessions.local import LocalSession
from finorch.sessions.ozstar import OzStarSession

session_map = {
    LocalSession.callsign: LocalSession,
    OzStarSession.callsign: OzStarSession,
    CITSession.callsign: CITSession
}
