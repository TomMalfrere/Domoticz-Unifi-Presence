from unittest import TestCase
from unittest.mock import patch, MagicMock, call

import requests
import sys
import os
import tempfile
import shutil

from types import SimpleNamespace

import plugin as unifi_domoticz_plugin

# Add the tests directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fakeDomoticz
sys.modules['Domoticz'] = fakeDomoticz


class TestPlugin(TestCase):
    
    def setUp(self):
        # Prepare a temporary home folder for the plugin to create devicetable.txt
        self.path_tmpdir = tempfile.mkdtemp()
        self.path_homefolder = self.path_tmpdir + os.sep

        # Patch module-level objects used by onStart
        unifi_domoticz_plugin.Parameters = {
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
        
        unifi_domoticz_plugin.Domoticz = self.domoticz
        # Ensure Images and Devices dicts exist and use fakeDomoticz ones
        unifi_domoticz_plugin.Images = fakeDomoticz.Images
        unifi_domoticz_plugin.Devices = fakeDomoticz.Devices
        self._orig_update_device = unifi_domoticz_plugin.UpdateDevice
        unifi_domoticz_plugin.UpdateDevice = fakeDomoticz.UpdateDevice

        # Make Domoticz.Image call fakeDomoticz.Image
        self.domoticz.Image.side_effect = lambda zip: fakeDomoticz.Image(zip)

        # Make Domoticz.Device call fakeDomoticz.Device
        self.domoticz.Device = MagicMock(side_effect = fakeDomoticz.Device)
        self.domoticz.Debug = MagicMock()
        self.domoticz.Log = MagicMock()
        self.domoticz.Error = MagicMock()

        # Create plugin instance and stub out login to avoid network calls
        self.plugin = unifi_domoticz_plugin.BasePlugin()

        
    
    def tearDown(self):
        # Clean up
        unifi_domoticz_plugin.UpdateDevice = self._orig_update_device
        unifi_domoticz_plugin.Images.clear()
        unifi_domoticz_plugin.Devices.clear()
        shutil.rmtree(self.path_tmpdir)

    def test_dummy(self):
        """Dummy test."""
        always_right = True
        self.assertTrue(always_right)
        
    def test_init(self):
        """Test plugin initialization."""
        self.assertIsInstance(self.plugin, unifi_domoticz_plugin.BasePlugin)
        self.assertEqual(self.plugin._Off_Delay, 60)
        self.assertEqual(self.plugin._log_devices, False)
        
    def test_onStart(self):
        self.plugin.login = MagicMock()
        self.domoticz.Heartbeat = MagicMock()
        # onStart checks 2 devices: UNIFI_OFF_DELAY and UNIFI_UPDATE_LOG, so we need to ensure they exist in Devices
        unifi_domoticz_plugin.Devices[self.plugin.UNIFI_OFF_DELAY] = MagicMock()
        unifi_domoticz_plugin.Devices[self.plugin.UNIFI_OFF_DELAY].nValue = 10
        unifi_domoticz_plugin.Devices[self.plugin.UNIFI_UPDATE_LOG] = MagicMock()
        unifi_domoticz_plugin.Devices[self.plugin.UNIFI_UPDATE_LOG].sValue = "On"
        self.assertEqual(len(unifi_domoticz_plugin.Images), 0)
        self.assertEqual(len(unifi_domoticz_plugin.Devices), 2)

        self.plugin.onStart()

        self.assertEqual(len(unifi_domoticz_plugin.Images), 3)
        self.assertEqual(len(unifi_domoticz_plugin.Devices), 5)
        self.plugin.login.assert_called()
        self.assertEqual(self.plugin._Off_Delay, 10 + 20)
        self.assertEqual(self.plugin._log_devices, True)
        self.assertEqual(self.plugin.versionCheck, True)
        self.domoticz.Heartbeat.assert_called_with(5)
        self.assertTrue(os.path.isfile(os.path.join(self.path_homefolder, "devicetable.txt")))

        self.plugin.login.reset_mock()
        self.domoticz.Heartbeat.reset_mock()
        unifi_domoticz_plugin.Parameters["Mode6"] = "20"
        unifi_domoticz_plugin.Images.clear()
        unifi_domoticz_plugin.Devices.clear()
        unifi_domoticz_plugin.Devices[self.plugin.UNIFI_OFF_DELAY] = MagicMock()
        unifi_domoticz_plugin.Devices[self.plugin.UNIFI_OFF_DELAY].nValue = 0
        unifi_domoticz_plugin.Devices[self.plugin.UNIFI_UPDATE_LOG] = MagicMock()
        unifi_domoticz_plugin.Devices[self.plugin.UNIFI_UPDATE_LOG].sValue = "Off"
        self.assertEqual(len(unifi_domoticz_plugin.Images), 0)
        self.assertEqual(len(unifi_domoticz_plugin.Devices), 2)

        self.plugin.onStart()

        self.assertEqual(len(unifi_domoticz_plugin.Images), 3)
        self.assertEqual(len(unifi_domoticz_plugin.Devices), 5)
        self.plugin.login.assert_called()
        self.assertEqual(self.plugin._Off_Delay, 0)
        self.assertEqual(self.plugin._log_devices, False)
        self.assertEqual(self.plugin.versionCheck, True)
        self.domoticz.Heartbeat.assert_called_with(5)
        self.assertTrue(os.path.isfile(os.path.join(self.path_homefolder, "devicetable.txt")))

    def test_onStart_on_old_domoticz(self):
        self.plugin.login = MagicMock()
        self.domoticz.Heartbeat = MagicMock()
        unifi_domoticz_plugin.Parameters["DomoticzVersion"] = "2019.1"

        self.plugin.onStart()

        self.plugin.login.assert_not_called()
        self.assertEqual(self.plugin._Off_Delay, 60)
        self.assertFalse(self.plugin._log_devices)
        self.assertEqual(self.plugin.versionCheck, False)
        self.domoticz.Heartbeat.assert_not_called()
        self.assertFalse(os.path.isfile(os.path.join(self.path_homefolder, "devicetable.txt")))

    def test_onStart_with_exception(self):
        self.plugin.login = MagicMock()
        self.domoticz.Heartbeat = MagicMock()
        unifi_domoticz_plugin.Parameters["DomoticzVersion"] = ""
        
        self.plugin.onStart()

        self.plugin.login.assert_not_called()
        self.assertEqual(self.plugin._Off_Delay, 60)
        self.assertFalse(self.plugin._log_devices)
        self.assertEqual(self.plugin.versionCheck, False)
        self.domoticz.Heartbeat.assert_not_called()
        self.assertFalse(os.path.isfile(os.path.join(self.path_homefolder, "devicetable.txt")))

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
        unifi_domoticz_plugin.DumpHTTPResponseToLog = MagicMock()
        self.plugin._current_status_code = 200
        self.plugin.onMessage(connection, data)
        
        self.plugin.onHeartbeat.assert_called()
       
        self.plugin.onHeartbeat.reset_mock()
        self.plugin._current_status_code = 500
        self.plugin.onMessage(connection, data)
        self.plugin.onHeartbeat.assert_not_called()

        # No exceptions should be raised, and no specific behavior to assert

    def test_onCommand(self):
        self.plugin.versionCheck = True
        self.plugin.onHeartbeat = MagicMock()
        # Call onCommand with dummy parameters
        unit = 1
        command = "On"
        level = 50
        hue = 100
        # current_status_code: 200
        self.plugin._current_status_code = None
        self.plugin.onCommand(unit, command, level, hue)
        self.plugin.onHeartbeat.assert_called()

        # current_status_code: 200
        # self.plugin.onHeartbeat.reset_mock()
        # self.plugin._current_status_code = 200
        # self.plugin.onCommand(unit, command, level, hue)
        # self.plugin.onHeartbeat.assert_called()


    def test_onNotification(self):
        # Call onNotification with dummy parameters
        name = "Test Notification"
        subject = "Test Subject"
        text = "This is a test notification."
        status = "Info"
        priority = 1
        sound = "Default"
        image = "image_data"
        
        self.plugin.onNotification( name, subject, text, status, priority, sound, image)
        
        self.domoticz.Debug.assert_called_with("onNotification: called")
        self.domoticz.Log.assert_called()

    def test_onDisconnect(self):
        # Call onDisconnect with dummy parameters
        connection = MagicMock()
        
        self.plugin.onDisconnect(connection)
        
        self.domoticz.Debug.assert_called_with("onDisconnect: called")
        
    def test_onHeartbeat(self):
        # Provide Devices entries for Off Delay (2) and Update Log (3)
        devices = {2: SimpleNamespace(nValue=10, sValue="10"),
                   3: SimpleNamespace(nValue=0, sValue="Off"),
        }
        unifi_domoticz_plugin.Devices.update(devices)

        # test with versionCheck False
        self.plugin.versionCheck = False
        self.plugin.onHeartbeat()
        self.domoticz.Debug.assert_called_with("onHeartbeat: called")
        self.domoticz.Log.assert_not_called()
        
        # test with versionCheck True and _current_status_code None
        self.domoticz.Debug.reset_mock()
        self.domoticz.Log.reset_mock()
        self.domoticz.Error.reset_mock()
        self.plugin.versionCheck = True
        self.plugin._current_status_code = None
        self.plugin.onHeartbeat()
        expected = [call("onHeartbeat: called"), 
                    call("login: called")]
        self.domoticz.Debug.assert_has_calls(expected)
        expected = [call("onHeartbeat: Attempting to reconnect Unifi Controller")]
        self.domoticz.Log.assert_has_calls(expected)

        # test with versionCheck True 
        #       _current_status_code 200
        #       Matrix[0][3] = "Off"
        self.domoticz.Debug.reset_mock()
        self.domoticz.Log.reset_mock()
        self.domoticz.Error.reset_mock()
        self.plugin.versionCheck = True
        self.plugin._current_status_code = 200
        # Initialize Matrix as a 2D list since it's not set by InitAfterLogin in test
        self.plugin.Matrix = [["OverRide", 
                               "00:00:00:00:00:00", 
                               255, 
                               "Off", 
                               "No", 
                               "No", 
                               None, 
                               None]]
        self.plugin.Matrix[0][3] = "Off"
        self.plugin.request_details = MagicMock()
        self.plugin.request_online_phones = MagicMock()
        self.plugin.onHeartbeat()
        expected = [call("onHeartbeat: called"), 
                    call('onHeartbeat: Requesting Unifi Controller details')]
        self.domoticz.Debug.assert_has_calls(expected)
        expected = []
        self.domoticz.Log.assert_has_calls(expected)
        
        # test with versionCheck True 
        #       _current_status_code 200
        #       Matrix[0][3] = "On"
        self.domoticz.Debug.reset_mock()
        self.domoticz.Log.reset_mock()
        self.domoticz.Error.reset_mock()
        self.plugin.Matrix[0][3] = "On"
        self.plugin.request_details.reset_mock()
        self.plugin.request_online_phones.reset_mock()
        unifi_domoticz_plugin.Devices[self.plugin.UNIFI_OFF_DELAY] = MagicMock()
        unifi_domoticz_plugin.Devices[self.plugin.UNIFI_OFF_DELAY].nValue = 10
        unifi_domoticz_plugin.Devices[255] = MagicMock()
        unifi_domoticz_plugin.Devices[255].LastUpdate = '2023-01-01 12:00:00'
        self.plugin.onHeartbeat()
        expected = [call("onHeartbeat: Requesting Unifi Controller details")]
        self.domoticz.Debug.assert_has_calls(expected)
        self.assertEqual(self.plugin.Matrix[0][3], "Off")
        self.assertEqual(self.plugin.Matrix[0][4], "Yes")
        self.plugin.request_details.assert_called()
        self.plugin.request_online_phones.assert_called()
        
        # test with versionCheck True 
        #       _current_status_code 200
        #       Matrix[0][3] = "On"
        self.domoticz.Debug.reset_mock()
        self.domoticz.Log.reset_mock()
        self.domoticz.Error.reset_mock()
        self.plugin.Matrix[0][3] = "On"
        self.plugin.request_details.reset_mock()
        self.plugin.request_online_phones.reset_mock()
        unifi_domoticz_plugin.Devices[self.plugin.UNIFI_OFF_DELAY] = MagicMock()
        unifi_domoticz_plugin.Devices[self.plugin.UNIFI_OFF_DELAY].nValue = 0
        unifi_domoticz_plugin.Devices[255] = MagicMock()
        unifi_domoticz_plugin.Devices[255].LastUpdate = '2023-01-01 12:00:00'
        self.plugin.onHeartbeat()
        expected = [call("onHeartbeat: Requesting Unifi Controller details")]
        self.domoticz.Debug.assert_has_calls(expected)
        self.assertEqual(self.plugin.Matrix[0][3], "Off")
        self.assertEqual(self.plugin.Matrix[0][4], "Yes")
        self.plugin.request_details.assert_called()
        self.plugin.request_online_phones.assert_called()
        
    def test_getCookies(self):
        mocked_cookie_jar = MagicMock()
        mocked_cookie_jar.get_dict.return_value = {'a': '1', 'b': '2'}
        
        # Call getCookies
        cookies = self.plugin.getCookies(mocked_cookie_jar, "example.com")
        
        #self.domoticz.Debug.assert_called_with("getCookies: called")
        self.domoticz.Log.assert_not_called()
        self.assertIsInstance(cookies, str)
        parts = cookies.split(';')
        self.assertEqual(set(parts), {'a=1', 'b=2'})
        
    def test_login(self):
        self.plugin.InitAfterLogin = MagicMock()
        
        # test successful login on unificontroller
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.cookies = MagicMock()
        mock_response.headers = {}
        mock_session.post.return_value = mock_response
        with patch('plugin.Session', return_value=mock_session):
            self.plugin.login()
            
            self.domoticz.Debug.assert_called_with("login: called")
            self.domoticz.Log.assert_called_with("login: Login successful into Unifi Controller")
            self.domoticz.Error.assert_not_called()
            # Verify post was called
            mock_session.post.assert_called_once()

        # test failed login with 400
        self.domoticz.Debug.reset_mock()
        self.domoticz.Log.reset_mock()
        self.domoticz.Error.reset_mock()
        self.plugin.InitAfterLogin.reset_mock()
        mock_session.reset_mock()
        mock_response.reset_mock()
        mock_response.status_code = 400
        mock_response.cookies.reset_mock()
        mock_response.headers = {}
        mock_session.post.return_value = mock_response
        with patch('plugin.Session', return_value=mock_session):
            self.plugin.login()
            
            self.domoticz.Debug.assert_called_with("login: called")
            self.domoticz.Log.assert_not_called()
            self.domoticz.Error.assert_called_with('login: Failed to log in to api (Unifi Controller) with provided credentials (400)')
            # Verify post was called
            mock_session.post.assert_called_once()

        # test failed login with 401
        self.domoticz.Debug.reset_mock()
        self.domoticz.Log.reset_mock()
        self.domoticz.Error.reset_mock()
        self.plugin.InitAfterLogin.reset_mock()
        mock_session.reset_mock()
        mock_response.reset_mock()
        mock_response.status_code = 401
        mock_response.cookies.reset_mock()
        mock_response.headers = {}
        mock_session.post.return_value = mock_response
        with patch('plugin.Session', return_value=mock_session):
            # first login attempt
            self.plugin.login()
            self.domoticz.Debug.assert_called_with("login: called")
            self.domoticz.Log.assert_called_with('login: First attempt failed to login to the Unifi Controller(URL=https://127.0.0.1:8443) with errorcode 401')
            self.domoticz.Error.assert_not_called()
            # Verify post was called
            mock_session.post.assert_called_once()

            # second login attempt
            self.domoticz.Debug.reset_mock()
            self.domoticz.Log.reset_mock()
            self.domoticz.Error.reset_mock()
            mock_session.post.reset_mock()
            self.plugin.login()
            self.domoticz.Debug.assert_called_with("login: called")
            self.domoticz.Log.assert_not_called()
            self.domoticz.Error.assert_called_with('login: Failed to login to the Unifi Controller with errorcode 401')
            # Verify post was called
            mock_session.post.assert_called_once()
            
        # test successful login on dreammachinepro
        unifi_domoticz_plugin.Parameters["Mode4"] = "dreammachinepro"
        self.domoticz.Debug.reset_mock()
        self.domoticz.Log.reset_mock()
        self.domoticz.Error.reset_mock()
        mock_session.reset_mock()
        mock_response.reset_mock()
        mock_response.status_code = 200
        mock_response.cookies.reset_mock()
        mock_response.headers = {'X-CSRF-Token': 'mock_csrf_token'}
        mock_session.post.return_value = mock_response
        with patch('plugin.Session', return_value=mock_session):
            self.plugin.login()
            
            self.domoticz.Debug.assert_called_with("login: called")
            self.domoticz.Log.assert_called_with('login: Login successful into Dream Machine Pro')
            self.domoticz.Error.assert_not_called()
            # Verify post was called
            mock_session.post.assert_called_once()

        # test successful login on something else
        unifi_domoticz_plugin.Parameters["Mode4"] = "somethingelse"
        self.domoticz.Debug.reset_mock()
        self.domoticz.Log.reset_mock()
        self.domoticz.Error.reset_mock()
        mock_session.reset_mock()
        mock_response.reset_mock()
        mock_response.status_code = 200
        mock_response.cookies.reset_mock()
        mock_response.headers = {'X-CSRF-Token': 'mock_csrf_token'}
        mock_session.post.return_value = mock_response
        with patch('plugin.Session', return_value=mock_session):
            self.plugin.login()
            self.domoticz.Debug.assert_called_with("login: called")
            self.domoticz.Log.assert_not_called()
            self.domoticz.Error.assert_called_once_with("login: Check configuration!!")
            # Verify post call was not made
            mock_session.post.assert_not_called()

    def test_login_post_read_timeout_exception(self):
        """Logout should handle requests.exceptions.ReadTimeout without closing session."""
        self.plugin.InitAfterLogin = MagicMock()
        
        # test successful login on unificontroller
        mock_session = MagicMock()
        # Simulate ReadTimeout when posting logout
        mock_session.post = MagicMock(side_effect=requests.exceptions.ReadTimeout("timeout"))
        with patch('plugin.Session', return_value=mock_session):
            self.plugin.login()
            
            self.domoticz.Debug.assert_called_with("login: called")
            self.domoticz.Log.assert_not_called()
            self.domoticz.Error.assert_called_once_with('Request to unificontroller timed out.')
            # Verify post was called
            mock_session.post.assert_called_once()
            self.assertEqual(self.plugin._current_status_code, 999)

    def test_login_post_connection_error_exception(self):
        """Logout should handle requests.exceptions.ConnectionError without closing session."""
        self.plugin.InitAfterLogin = MagicMock()
        
        # test successful login on unificontroller
        mock_session = MagicMock()
        # Simulate ReadTimeout when posting logout
        mock_session.post = MagicMock(side_effect=requests.exceptions.ConnectionError("timeout"))
        with patch('plugin.Session', return_value=mock_session):
            self.plugin.login()
            
            self.domoticz.Debug.assert_called_with("login: called")
            self.domoticz.Log.assert_not_called()
            self.domoticz.Error.assert_called_once_with('Connection refused to unificontroller')
            # Verify post was called
            mock_session.post.assert_called_once()
            self.assertEqual(self.plugin._current_status_code, 999)

    def test_login_post_http_error_exception(self):
        """Logout should handle requests.exceptions.HTTPError without closing session."""
        self.plugin.InitAfterLogin = MagicMock()
        
        mock_session = MagicMock()
        # Simulate ReadTimeout when posting logout
        mock_session.post = MagicMock(side_effect=requests.exceptions.HTTPError("HTTPError"))
        with patch('plugin.Session', return_value=mock_session):
            self.plugin.login()
            
            self.domoticz.Debug.assert_called_with("login: called")
            self.domoticz.Log.assert_not_called()
            self.domoticz.Error.assert_called_once_with("Login failed. If it's first attempt then ok, otherwise there is something wrong: HTTPError")
            # Verify post was called
            mock_session.post.assert_called_once()
            self.assertIsNone(self.plugin._current_status_code)
                
    def test_logout(self):
        self.plugin._session.post = MagicMock()
        self.plugin._session.close = MagicMock()
        self.plugin._baseurl = "https://baseurl"
        self.plugin._timeout_timer = None
  
        # test with _current_status_code None      
        self.domoticz.Debug.reset_mock()
        self.domoticz.Log.reset_mock()
        self.domoticz.Error.reset_mock()
        self.plugin._session.post.reset_mock()
        self.plugin._session.close.reset_mock()
        self.plugin._current_status_code = None
        self.plugin.logout()
        #self.domoticz.Debug.assert_called_with("logout: called")
        self.domoticz.Log.assert_not_called()
        self.domoticz.Error.assert_not_called()
        self.plugin._session.post.assert_not_called()
        self.plugin._session.close.assert_not_called()
        self.assertEqual(self.plugin._current_status_code, None)

        # test with status code 200
        # Parameters["Mode4"] = "unificontroller"
        self.domoticz.Debug.reset_mock()
        self.domoticz.Log.reset_mock()
        self.domoticz.Error.reset_mock()
        self.plugin._session.post.reset_mock()
        self.plugin._session.close.reset_mock()
        self.plugin._current_status_code = 200
        self.plugin.logout()
        #self.domoticz.Debug.assert_called_with("logout: called")
        self.domoticz.Log.assert_called_with('logout: Logout of the Unifi API')
        self.domoticz.Error.assert_not_called()
        self.plugin._session.post.assert_called_with("https://baseurl/logout")
        self.plugin._session.close.assert_called()
        self.assertEqual(self.plugin._current_status_code, 999)
        self.assertIsNone(self.plugin._timeout_timer)
        
        # test with status code 200
        # Parameters["Mode4"] = "dreammachinepro"
        self.domoticz.Debug.reset_mock()
        self.domoticz.Log.reset_mock()
        self.domoticz.Error.reset_mock()
        self.plugin._session.post.reset_mock()
        self.plugin._session.close.reset_mock()
        self.plugin._current_status_code = 200
        unifi_domoticz_plugin.Parameters["Mode4"] = "dreammachinepro"
        self.plugin.logout()
        #self.domoticz.Debug.assert_called_with("logout: called")
        self.domoticz.Log.assert_called_with('logout: Logout of the Unifi API')
        self.domoticz.Error.assert_not_called()
        self.plugin._session.post.assert_called_with("https://baseurl/api/auth")
        self.plugin._session.close.assert_called()
        self.assertEqual(self.plugin._current_status_code, 999)
        self.assertIsNone(self.plugin._timeout_timer)

        # test with status code 200
        # Parameters["Mode4"] = "something else"
        self.domoticz.Debug.reset_mock()
        self.domoticz.Log.reset_mock()
        self.domoticz.Error.reset_mock()
        self.plugin._session.post.reset_mock()
        self.plugin._session.close.reset_mock()
        self.plugin._current_status_code = 200
        unifi_domoticz_plugin.Parameters["Mode4"] = "something else"
        self.plugin.logout()
        #self.domoticz.Debug.assert_called_with("logout: called")
        self.domoticz.Log.assert_called_with('logout: Logout of the Unifi API')
        self.domoticz.Error.assert_called_with("Check configuration!!")
        self.plugin._session.post.assert_not_called()
        self.plugin._session.close.assert_called()
        self.assertEqual(self.plugin._current_status_code, 999)
        self.assertIsNone(self.plugin._timeout_timer)

        # test with status code 404
        self.domoticz.Debug.reset_mock()
        self.domoticz.Log.reset_mock()
        self.domoticz.Error.reset_mock()
        self.plugin._session.post.reset_mock()
        self.plugin._session.close.reset_mock()
        self.plugin._current_status_code = 404
        self.plugin.logout()
        #self.domoticz.Debug.assert_called_with("logout: called")
        self.domoticz.Log.assert_not_called()
        self.domoticz.Error.assert_not_called()
        self.plugin._session.post.assert_not_called()
        self.plugin._session.close.assert_not_called()
        self.assertEqual(self.plugin._current_status_code, 404)
        self.assertIsNone(self.plugin._timeout_timer)

    def test_logout_post_read_timeout_exception(self):
        """Logout should handle requests.exceptions.ReadTimeout without closing session."""
        # Simulate ReadTimeout when posting logout
        self.plugin._session.post = MagicMock(side_effect=requests.exceptions.ReadTimeout("timeout"))
        self.plugin._session.close = MagicMock()
        self.plugin._baseurl = "https://baseurl"
        unifi_domoticz_plugin.Parameters["Mode4"] = "unificontroller"
        self.plugin._current_status_code = 200

        self.plugin.logout()

        self.domoticz.Error.assert_called_with("Request to unificontroller timed out during logout.")
        self.plugin._session.close.assert_not_called()
        self.assertEqual(self.plugin._current_status_code, 200)

    def test_logout_post_connection_error_exception(self):
        """Logout should handle requests.exceptions.ConnectionError without closing session."""
        # Simulate ConnectionError when posting logout
        self.plugin._session.post = MagicMock(side_effect=requests.exceptions.ConnectionError("conn refused"))
        self.plugin._session.close = MagicMock()
        self.plugin._baseurl = "https://baseurl"
        unifi_domoticz_plugin.Parameters["Mode4"] = "dreammachinepro"
        self.plugin._current_status_code = 200

        self.plugin.logout()

        self.domoticz.Error.assert_called_with("Connection refused to dreammachinepro during logout.")
        self.plugin._session.close.assert_not_called()
        self.assertEqual(self.plugin._current_status_code, 200)

    def test_logout_post_connect_timeout_exception(self):
        """Logout should handle requests.exceptions.ConnectTimeout without closing session."""
        # Simulate ConnectionError when posting logout
        self.plugin._session.post = MagicMock(side_effect=requests.exceptions.HTTPError("HTTPError"))
        self.plugin._session.close = MagicMock()
        self.plugin._baseurl = "https://baseurl"
        self.plugin._current_status_code = 200

        self.plugin.logout()

        self.domoticz.Error.assert_called_with('Logout failure: HTTPError')
        self.plugin._session.close.assert_not_called()
        self.assertEqual(self.plugin._current_status_code, 200)
        
    def test_InitAfterLogin(self):
        self.plugin.detectUnifiDevices = MagicMock()
        # self.plugin.create_devices = MagicMock()
        
        unifi_domoticz_plugin.Parameters["Mode2"] = "Phone1=aa:bb:cc:dd:ee:ff,Phone2=11:22:33:44:55:66"
        
        # test with _current_status_code None      
        self.domoticz.Debug.reset_mock()
        self.domoticz.Log.reset_mock()
        self.domoticz.Error.reset_mock()
        self.plugin._current_status_code = None        
        self.plugin.InitAfterLogin()
        self.plugin.detectUnifiDevices.assert_not_called()
        # self.plugin.create_devices.assert_not_called()
        self.domoticz.Debug.assert_not_called()
        self.domoticz.Log.assert_not_called()
        self.domoticz.Error.assert_not_called()
        
        # test with _current_status_code 200      
        self.domoticz.Debug.reset_mock()
        self.domoticz.Log.reset_mock()
        self.domoticz.Error.reset_mock()

        self.assertEqual(len(unifi_domoticz_plugin.Images), 0)
        #self.assertEqual(len(unifi_domoticz_plugin.Devices), 2)
        
        # mocks for login()
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.cookies = MagicMock()
        mock_response.headers = {}
        mock_session.post.return_value = mock_response
        with patch('plugin.Session', return_value=mock_session):
            # call onStart -> login -> InitAfterLogin -> create_devices
            self.plugin.onStart()        

        self.assertEqual(len(unifi_domoticz_plugin.Images), 3)
        #self.assertEqual(len(unifi_domoticz_plugin.Devices), 5)

        self.plugin.detectUnifiDevices.assert_called()
        # self.plugin.create_devices.assert_called()
        expected = [call("onStart:  called"),
                    call("login: called")]
        self.domoticz.Debug.assert_has_calls(expected, any_order=True)
        self.domoticz.Log.assert_called()
        self.domoticz.Error.assert_not_called()
        
        # self.domoticz.Debug.reset_mock()
        # self.domoticz.Log.reset_mock()
        
        # self.plugin._current_status_code = 200
        
        # self.plugin.InitAfterLogin()
        
        # self.plugin.detectUnifiDevices.assert_called()
        # self.plugin.create_devices.assert_called()
        
        # self.domoticz.Debug.assert_called_with("InitAfterLogin: called")
        # self.domoticz.Log.assert_not_called()

    # def test_create_devices(self):
    #     self.domoticz.Device = MagicMock()
        
    #     # Call create_devices
    #     self.plugin.create_devices()

    def test_setVersionCheck(self):
        # Call setVersionCheck
        self.plugin.setVersionCheck(True, "Test Note")
        self.assertTrue(self.plugin.versionCheck)
        
        self.plugin.setVersionCheck(False, "Test Note")
        self.assertFalse(self.plugin.versionCheck)

    def test_create_devicetable(self):
        pass

    def test_create_devices(self):
        # mocks for onStart
        # self.plugin.login = MagicMock()
        self.domoticz.Heartbeat = MagicMock()
        self.assertEqual(len(unifi_domoticz_plugin.Images), 0)
        self.assertEqual(len(unifi_domoticz_plugin.Devices), 0)

        # mocks for login()
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.cookies = MagicMock()
        mock_response.headers = {}
        mock_session.post.return_value = mock_response
        with patch('plugin.Session', return_value=mock_session):
            # call onStart -> login -> InitAfterLogin -> create_devices
            self.plugin.onStart()        
        
        self.assertEqual(len(unifi_domoticz_plugin.Images), 3)
        self.assertEqual(len(unifi_domoticz_plugin.Devices), 8)
        self.assertIn(self.plugin.UNIFI_ANYONE_HOME_UNIT, unifi_domoticz_plugin.Devices)
        self.assertIn(self.plugin.UNIFI_OVERRIDE_UNIT, unifi_domoticz_plugin.Devices)
        self.assertIn(50, unifi_domoticz_plugin.Devices) # 50-70 are reserved for phone devices
        self.assertEqual(unifi_domoticz_plugin.Devices[50].Name, "Phone1")
        
        expected = [call("onStart:  called")]
        self.domoticz.Debug.assert_has_calls(expected)
        expected = [call("create_devices: Plugin Name = ")]
        self.domoticz.Log.assert_has_calls(expected)
        