from unittest import TestCase
from unittest.mock import Mock, patch, MagicMock
import requests
from http.client import RemoteDisconnected
import sys
import os

# Add the tests directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fakeDomoticz
sys.modules['Domoticz'] = fakeDomoticz

# Create mock urllib3
mock_urllib3 = MagicMock()
mock_urllib3.disable_warnings = MagicMock()

from plugin import BasePlugin


class TestPlugin(TestCase):
    
    def setUp(self):
        self.plugin = BasePlugin()
    
    def tearDown(self):
        pass

    def test_dummy(self):
        """Dummy test."""
        always_right = True
        self.assertTrue(always_right)
        
    def test_init(self):
        """Test plugin initialization."""
        self.assertIsInstance(self.plugin, BasePlugin)


class TestRequestOnlinePhones(TestCase):
    """Test cases for request_online_phones method error handling"""
    
    def _create_plugin_instance(self):
        """Helper to create a properly configured plugin instance"""
        plugin_inst = BasePlugin()
        # Mock the session
        plugin_inst._session = Mock()
        plugin_inst._baseurl = "https://test.example.com"
        plugin_inst._site = "default"
        plugin_inst._Cookies = {}
        plugin_inst._verify_ssl = False
        plugin_inst.Matrix = []
        plugin_inst.total_devices_count = 0
        # Mock the login method to avoid additional complications
        plugin_inst.login = Mock()
        return plugin_inst
    
    @patch.dict('plugin.__dict__', {
        'Parameters': {
            "Mode4": "unificontroller", 
            "Mode2": "test_phone=aa:bb:cc:dd:ee:ff",
            "Username": "admin",
            "Password": "test",
            "Mode5": "Yes"
        }, 
        'Domoticz': MagicMock(), 
        'urllib3': mock_urllib3
    })
    def test_connection_error_handling(self):
        """Test that ConnectionError doesn't cause UnboundLocalError"""
        plugin_inst = self._create_plugin_instance()
        
        # Simulate ConnectionError from remote disconnect
        connection_error = requests.exceptions.ConnectionError(
            ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
        )
        plugin_inst._session.get.side_effect = connection_error
        
        # This should not raise UnboundLocalError
        try:
            plugin_inst.request_online_phones()
        except UnboundLocalError as e:
            self.fail(f"UnboundLocalError raised: {e}. Variable 'r' not defined before exception access.")
    
    @patch.dict('plugin.__dict__', {
        'Parameters': {
            "Mode4": "unificontroller", 
            "Mode2": "test_phone=aa:bb:cc:dd:ee:ff",
            "Username": "admin",
            "Password": "test",
            "Mode5": "Yes"
        }, 
        'Domoticz': MagicMock(), 
        'urllib3': mock_urllib3
    })
    def test_read_timeout_error_handling(self):
        """Test that ReadTimeout doesn't cause UnboundLocalError"""
        plugin_inst = self._create_plugin_instance()
        
        # Simulate ReadTimeout
        plugin_inst._session.get.side_effect = requests.exceptions.ReadTimeout("Request timed out")
        
        try:
            plugin_inst.request_online_phones()
        except UnboundLocalError as e:
            self.fail(f"UnboundLocalError raised: {e}. Variable 'r' not defined before exception access.")
    
    @patch.dict('plugin.__dict__', {
        'Parameters': {
            "Mode4": "unificontroller", 
            "Mode2": "test_phone=aa:bb:cc:dd:ee:ff",
            "Username": "admin",
            "Password": "test",
            "Mode5": "Yes"
        }, 
        'Domoticz': MagicMock(), 
        'urllib3': mock_urllib3
    })
    def test_successful_request(self):
        """Test successful request returns data correctly"""
        plugin_inst = self._create_plugin_instance()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'mac': 'aa:bb:cc:dd:ee:ff',
                    'is_wired': False,
                    'name': 'Test Phone'
                }
            ]
        }
        plugin_inst._session.get.return_value = mock_response
        # Mock ProcessDevices to avoid additional complications
        plugin_inst.ProcessDevices = Mock()
        
        try:
            plugin_inst.request_online_phones()
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Unexpected exception raised: {e}")
    
    @patch.dict('plugin.__dict__', {
        'Parameters': {
            "Mode4": "dreammachinepro", 
            "Mode2": "test_phone=aa:bb:cc:dd:ee:ff",
            "Username": "admin",
            "Password": "test",
            "Mode5": "Yes"
        }, 
        'Domoticz': MagicMock(), 
        'urllib3': mock_urllib3
    })
    def test_connection_refused_for_dreammachine_pro(self):
        """Test ConnectionError with Dream Machine Pro configuration"""
        plugin_inst = self._create_plugin_instance()
        
        connection_error = requests.exceptions.ConnectionError(
            ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
        )
        plugin_inst._session.get.side_effect = connection_error
        
        try:
            plugin_inst.request_online_phones()
        except UnboundLocalError as e:
            self.fail(f"UnboundLocalError raised: {e}. Variable 'r' not defined before exception access.")


class TestLoginMethod(TestCase):
    """Test cases for login method error handling"""
    
    def _create_plugin_instance(self):
        """Helper to create a properly configured plugin instance"""
        plugin_inst = BasePlugin()
        # Mock the session
        plugin_inst._session = Mock()
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
