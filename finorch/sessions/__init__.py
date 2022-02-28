from finorch.sessions.cit import CITSession
from finorch.sessions.local import LocalSession
from finorch.sessions.ozstar import OzStarSession
from finorch.sessions.ssh import SshSession

session_map = {
    LocalSession.callsign: LocalSession,
    OzStarSession.callsign: OzStarSession,
    CITSession.callsign: CITSession,
    SshSession.callsign: SshSession
}
