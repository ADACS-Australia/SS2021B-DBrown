import os
import pathlib
from configparser import ConfigParser
from pathlib import Path

import appdirs

APPNAME = "finorch"
APPAUTHOR = "ADACS"


class _ConfigManager:
    """
    Used as a utility wrapper around the configuration ini files to make reading/writing configuration easier
    """

    def __init__(self, ini_file):
        self._ini_file = ini_file
        self._config = ConfigParser()

        # Read the configuration if possible
        self._read()

    @staticmethod
    def get_log_directory():
        """
        Gets the path to the log directory (And checks that the log directory exists)

        :return: A Path object representing the log directory.
        """
        p = Path(appdirs.user_config_dir(APPNAME, APPAUTHOR)) / 'logs'
        os.makedirs(p, exist_ok=True)
        return p

    @staticmethod
    def get_config_directory():
        """
        Gets the path to the config directory (And checks that the config directory exists)

        :return: A Path object representing the config directory.
        """
        p = Path(appdirs.user_config_dir(APPNAME, APPAUTHOR))
        os.makedirs(p, exist_ok=True)
        return p

    def get_section(self, section):
        """
        Read the specific section from the configuration file and return the configuration as a dict

        :param section: The section to return as a dict
        :return: The section (if it exists) as a dict, if the section does not exist it returns None
        """
        config_dict = {
            s: dict(self._config.items(s)) for s in self._config.sections()
        }

        return config_dict.get(section, None)

    def set(self, section, option, value):
        """
        Updates the configuration file with the specified section, option, and value

        :param section: The configuration section
        :param option: The configuration option
        :param value: The value to set
        :return: None
        """
        if not self._config.has_section(section):
            self._config.add_section(section)

        self._config.set(section, option, str(value))
        self._save()

    def _save(self):
        """
        Saves the configuration object to the configuration file

        :return: None
        """
        with open(self._ini_file, 'w') as f:
            self._config.write(f)
            f.flush()

    def _read(self):
        """
        Rereads the configuration file in to the configuration object

        :return: None
        """
        self._config.read(self._ini_file)


class _ApiConfigManager(_ConfigManager):
    """
    Configuration Manager for the API.
    """

    def __init__(self):
        super().__init__(self.get_config_directory() / "api.ini")


class _ClientConfigManager(_ConfigManager):
    """
    Configuration Manager for the Client.
    """

    def __init__(self):
        super().__init__(self.get_config_directory() / "client.ini")

    def get_port(self):
        """
        Gets the clients last port

        :return: The last port the client was running on, or None
        """
        self._read()

        if section := self.get_section("main"):
            return section.get("port", None)

        return None

    def set_port(self, port):
        """
        Sets the clients current port

        :return: None
        """
        self._read()
        self.set("main", "port", port)


class WrapperConfigManager(_ConfigManager):
    """
    Configuration Manager for the Wrapper.
    """

    def __init__(self):
        super().__init__(pathlib.Path.cwd() / "wrapper.ini")

    def get_port(self):
        """
        Gets the wrapper's port

        :return: The port the wrapper is running on, or None
        """
        self._read()

        if section := self.get_section("main"):
            return section.get("port", None)

        return None

    def set_port(self, port):
        """
        Sets the clients current port

        :return: None
        """
        self._read()
        self.set("main", "port", port)


# Create a config manager singleton to avoid issues with concurrency
api_config_manager = _ApiConfigManager()
client_config_manager = _ClientConfigManager()
