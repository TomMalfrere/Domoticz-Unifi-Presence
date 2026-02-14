from unittest import TestCase
from unittest.mock import patch, MagicMock

import requests

from http.client import RemoteDisconnected

import plugin as unifi_domoticz_plugin

# Create mock urllib3
mock_urllib3 = MagicMock()
mock_urllib3.disable_warnings = MagicMock()


class TestLoginMethod(TestCase):
    """Test cases for login method error handling"""
    
    def _create_plugin_instance(self):
        """Helper to create a properly configured plugin instance"""
        plugin_inst = unifi_domoticz_plugin.BasePlugin()
        # Mock the session
        plugin_inst._session = MagicMock()
        plugin_inst._login_data = {}
        return plugin_inst
    
    @patch.dict('plugin.__dict__', {
        'Parameters': {
            "Mode4": "unificontroller",
            "Username": "admin",
            "Password": "test",
            "Address": "192.168.1.1",
            "Port": "8443",
            "Mode1": "default"
        },
        'Domoticz': MagicMock(),
        'urllib3': mock_urllib3
    })
    def test_login_connection_error_no_infinite_loop(self):
        """Test that ConnectionError in login doesn't cause infinite recursion"""
        plugin_inst = self._create_plugin_instance()
        
        # Simulate ConnectionError
        connection_error = requests.exceptions.ConnectionError(
            ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
        )
        plugin_inst._session.post.side_effect = connection_error
        
        # This should not raise UnboundLocalError or cause infinite recursion
        try:
            plugin_inst.login()
        except UnboundLocalError as e:
            self.fail(f"UnboundLocalError raised in login: {e}. Variable 'r' not defined.")
        except RecursionError:
            self.fail("RecursionError raised - infinite loop detected in login method.")
    
    @patch.dict('plugin.__dict__', {
        'Parameters': {
            "Mode4": "unificontroller",
            "Username": "admin",
            "Password": "test",
            "Address": "192.168.1.1",
            "Port": "8443",
            "Mode1": "default"
        },
        'Domoticz': MagicMock(),
        'urllib3': mock_urllib3
    })
    def test_login_read_timeout_error(self):
        """Test that ReadTimeout in login is handled properly"""
        plugin_inst = self._create_plugin_instance()
        
        # Simulate ReadTimeout
        plugin_inst._session.post.side_effect = requests.exceptions.ReadTimeout("Timeout")
        
        # Should not raise UnboundLocalError
        try:
            plugin_inst.login()
        except UnboundLocalError as e:
            self.fail(f"UnboundLocalError raised in login: {e}. Variable 'r' not defined.")

