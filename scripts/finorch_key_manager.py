import sys
from pathlib import Path

from finorch.config.config import api_config_manager
from finorch.sessions import session_map
from finorch.transport.ssh import SshTransport

SET_SSH_KEY_USAGE = """
Usage: set_ssh_key <session name> <private key>
    eg. set_ssh_key ozstar ~/keys/my_ozstar_key.pem
"""


REMOVE_SSH_KEY_USAGE = """
Usage: remove_ssh_key <session name>
    eg. remove_ssh_key ozstar
"""


def set_ssh_key():
    """
    Configures the private ssh key used to connect to the specified ssh transport session. The key is saved in the
    api configuration ini file.
    """
    # Check for the correct number of arguments
    if len(sys.argv) != 3:
        print(SET_SSH_KEY_USAGE)
        exit(1)

    # Check for a valid session and that the session uses SSH Transport
    session = sys.argv[1]
    if session not in session_map:
        print(f"{session} is not a valid session name.")
        exit(1)

    session_klass = session_map[session]
    print(session_klass.transport_klass is SshTransport)
    if session_klass.transport_klass is not SshTransport:
        print(f"{session} is not a session that utilises an SSH Transport.")
        exit(1)

    # Check that the key file exists and read it in
    key_file = sys.argv[2]
    if not Path(key_file).exists():
        print(f"{key_file} does not exist.")
        exit(1)

    key = open(key_file, 'r').read()

    api_config_manager.set('ozstar', 'key', key)

    print(f"SSH key for session {session} updated successfully.")

    # Report success
    exit(0)


def remove_ssh_key():
    """
    Removes any configured SSH key from the configuration for the specified session.
    """
    # Check for the correct number of arguments
    if len(sys.argv) != 2:
        print(REMOVE_SSH_KEY_USAGE)
        exit(1)

    # Check for a valid session and that the session uses SSH Transport
    session = sys.argv[1]
    if session not in session_map:
        print(f"{session} is not a valid session name.")
        exit(1)

    session_klass = session_map[session]
    print(session_klass.transport_klass is SshTransport)
    if session_klass.transport_klass is not SshTransport:
        print(f"{session} is not a session that utilises an SSH Transport.")
        exit(1)

    api_config_manager.set('ozstar', 'key', '')

    print(f"SSH key for session {session} removed successfully.")

    # Report success
    exit(0)
