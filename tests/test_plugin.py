import requests
import sys
import os
import tempfile
import shutil

from unittest import TestCase
from unittest.mock import Mock, patch, MagicMock, call
from http.client import RemoteDisconnected
from types import SimpleNamespace

import plugin as plugin_module


# Add the tests directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fakeDomoticz
sys.modules['Domoticz'] = fakeDomoticz

# Create mock urllib3
mock_urllib3 = MagicMock()
mock_urllib3.disable_warnings = MagicMock()

# from plugin import BasePlugin


class TestPlugin(TestCase):
    
    def setUp(self):
        # Prepare a temporary home folder for the plugin to create devicetable.txt
        self.path_tmpdir = tempfile.mkdtemp()
        self.path_homefolder = self.path_tmpdir + os.sep

        # Patch module-level objects used by onStart
        plugin_module.Parameters = {
            "DomoticzVersion": "2021.1",
            "HomeFolder": self.path_homefolder,
            "Mode1": "default",
            "Mode2": "Phone1=aa:bb:cc:dd:ee:ff",
            "Mode3": "No",
            "Mode4": "unificontroller",
            "Mode5": "No",
            "Mode6": "0",
            "Username": "user",
            "Password": "pass",
            "Address": "127.0.0.1",
            "Port": "8443",
        }

        # Provide a Domoticz mock that exposes the methods onStart calls
        self.domoticz = MagicMock()
        plugin_module.Domoticz = self.domoticz

        # Ensure Images dict exists
        plugin_module.Images = {}

        # Provide Devices entries for Off Delay (2) and Update Log (3)
        devices = {2: SimpleNamespace(nValue=10),
                   3: SimpleNamespace(sValue="Off"),
        }
        plugin_module.Devices = devices

        # Create plugin instance and stub out login to avoid network calls
        self.plugin = plugin_module.BasePlugin()
    
    def tearDown(self):
        # Clean up
        shutil.rmtree(self.path_tmpdir)

    def test_dummy(self):
        """Dummy test."""
        always_right = True
        self.assertTrue(always_right)
        
    def test_init(self):
        """Test plugin initialization."""
        self.assertIsInstance(self.plugin, plugin_module.BasePlugin)
        self.assertEqual(self.plugin._Off_Delay, 60)
        self.assertEqual(self.plugin._log_devices, False)
        
    def test_onStart(self):
        self.plugin.login = MagicMock()
        self.domoticz.Heartbeat = MagicMock()

        # Call onStart and verify expected behavior
        self.plugin.onStart()

        # login should be called
        self.plugin.login.assert_called()

        # Off delay should be set from Devices[2].nValue + 20
        self.assertEqual(self.plugin._Off_Delay, 10 + 20)

        # _log_devices should be False because Devices[3].sValue == "Off"
        self.assertFalse(self.plugin._log_devices)

        # Heartbeat should have been requested
        self.domoticz.Heartbeat.assert_called_with(5)

        # devicetable file should have been created
        self.assertTrue(os.path.isfile(os.path.join(self.path_homefolder, "devicetable.txt")))


    def test_onStop(self):
        self.plugin.logout = MagicMock()

        # Call onStop
        self.plugin.onStop()

        # logout should be called
        self.plugin.logout.assert_called()
        
    def test_onConnect(self):
        # Call onConnect with dummy parameters
        connection = MagicMock()
        status = 0
        description = "Test Description"
        self.plugin.onConnect(connection, status, description)

        # No exceptions should be raised, and no specific behavior to assert

    def test_onMessage(self):
        self.plugin.onHeartbeat = MagicMock()

        # Call onMessage with dummy parameters
        connection = MagicMock()
        # Provide the dict structure expected by onMessage
        data = {'Data': b'{}', 'Status': '200'}
        # Mock DumpHTTPResponseToLog to avoid exercising its implementation
        plugin_module.DumpHTTPResponseToLog = MagicMock()
        self.plugin._current_status_code = 200
        self.plugin.onMessage(connection, data)
        
        self.plugin.onHeartbeat.assert_called()
       
        self.plugin.onHeartbeat.reset_mock()
        self.plugin._current_status_code = 500
        self.plugin.onMessage(connection, data)
        self.plugin.onHeartbeat.assert_not_called()

        # No exceptions should be raised, and no specific behavior to assert

    def test_onCommand(self):
        # Call onCommand with dummy parameters
        unit = 1
        command = "On"
        level = 50
        hue = 100
        self.plugin.onCommand(unit, command, level, hue)

    def test_onNotification(self):
        # Call onNotification with dummy parameters
        name = "Test Notification"
        subject = "Test Subject"
        text = "This is a test notification."
        status = "Info"
        priority = 1
        sound = "Default"
        image = "image_data"
        
        self.domoticz.Log = MagicMock()
        self.domoticz.Debug = MagicMock()
        
        self.plugin.onNotification( name, subject, text, status, priority, sound, image)
        
        self.domoticz.Debug.assert_called_with("onNotification: called")
        self.domoticz.Log.assert_called()

    def test_onDisconnect(self):
        # Call onDisconnect with dummy parameters
        connection = MagicMock()
        self.domoticz.Debug = MagicMock()
        
        self.plugin.onDisconnect(connection)
        
        self.domoticz.Debug.assert_called_with("onDisconnect: called")
        
    def test_onHeartbeat(self):
        self.domoticz.Debug = MagicMock()
        self.domoticz.Log = MagicMock()
        
        self.plugin.versionCheck = False
        
        # Call onHeartbeat
        self.plugin.onHeartbeat()

        self.domoticz.Debug.assert_called_with("onHeartbeat: called")
        self.domoticz.Log.assert_not_called()
        
        self.domoticz.Debug.reset_mock()
        self.domoticz.Log.reset_mock()

        self.plugin.versionCheck = True
        self.plugin._current_status_code = None
        
        # Call onHeartbeat
        self.plugin.onHeartbeat()

        expected = [call("onHeartbeat: called"), 
                    call("login: called")]
        self.domoticz.Debug.assert_has_calls(expected)
        expected = [call("onHeartbeat: Attempting to reconnect Unifi Controller")]
        self.domoticz.Log.assert_has_calls(expected)

        # self.domoticz.Debug.reset_mock()
        # self.domoticz.Log.reset_mock()

        # self.plugin.versionCheck = True
        # self.plugin._current_status_code = 200
        
        # # Call onHeartbeat
        # self.plugin.onHeartbeat()

        # expected = [call("onHeartbeat: called"), 
        #             call("login: called")]
        # self.domoticz.Debug.assert_has_calls(expected)
        # expected = [call("onHeartbeat: Attempting to reconnect Unifi Controller")]
        # self.domoticz.Log.assert_has_calls(expected)

        # self.domoticz.Debug.reset_mock()
        # self.domoticz.Log.reset_mock()

        # self.plugin.versionCheck = True
        # self.plugin._current_status_code = 401
        
        # # Call onHeartbeat
        # self.plugin.onHeartbeat()

        # expected = [call("onHeartbeat: called"), 
        #             call("login: called")]
        # self.domoticz.Debug.assert_has_calls(expected)
        # expected = [call("onHeartbeat: Attempting to reconnect Unifi Controller")]
        # self.domoticz.Log.assert_has_calls(expected)

        # self.domoticz.Debug.reset_mock()
        # self.domoticz.Log.reset_mock()

        # self.plugin.versionCheck = True
        # self.plugin._current_status_code = 404
        
        # # Call onHeartbeat
        # self.plugin.onHeartbeat()

        # expected = [call("onHeartbeat: called"), 
        #             call("login: called")]
        # self.domoticz.Debug.assert_has_calls(expected)
        # expected = [call("onHeartbeat: Attempting to reconnect Unifi Controller")]
        # self.domoticz.Log.assert_has_calls(expected)
        
    def test_InitAfterLogin(self):
        self.plugin.detectUnifiDevices = MagicMock()
        self.plugin.create_devices = MagicMock()
        
        self.domoticz.Debug = MagicMock()
        self.domoticz.Log = MagicMock()
        
        # Call InitAfterLogin
        self.plugin.InitAfterLogin()
        
        self.plugin.detectUnifiDevices.assert_not_called()
        self.plugin.create_devices.assert_not_called()

        self.domoticz.Debug.assert_called_with("InitAfterLogin: called")
        self.domoticz.Log.assert_not_called()
        
        # self.domoticz.Debug.reset_mock()
        # self.domoticz.Log.reset_mock()
        
        # self.plugin._current_status_code = 200
        
        # self.plugin.InitAfterLogin()
        
        # self.plugin.detectUnifiDevices.assert_called()
        # self.plugin.create_devices.assert_called()
        
        # self.domoticz.Debug.assert_called_with("InitAfterLogin: called")
        # self.domoticz.Log.assert_not_called()

    def test_setVersionCheck(self):
        # Call setVersionCheck
        self.plugin.setVersionCheck(True, "Test Note")
        self.assertTrue(self.plugin.versionCheck)
        
        self.plugin.setVersionCheck(False, "Test Note")
        self.assertFalse(self.plugin.versionCheck)

class TestRequestOnlinePhones(TestCase):
    """Test cases for request_online_phones method error handling"""
    
    def _create_plugin_instance(self):
        """Helper to create a properly configured plugin instance"""
        plugin_inst = plugin_module.BasePlugin()
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
        plugin_inst = plugin_module.BasePlugin()
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

