from finorch.sessions.cit import CitSession
from finorch.sessions.local import LocalSession
from finorch.sessions.ozstar import OzStarSession

session_map = {
    LocalSession.callsign: LocalSession,
    OzStarSession.callsign: OzStarSession,
    CitSession.callsign: CitSession
}
