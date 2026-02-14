from unittest import TestCase
from unittest.mock import MagicMock

import plugin
import fakeDomoticz


class TestUpdateDevice(TestCase):
    """Test cases for UpdateDevice function"""
    
    def setUp(self):
        """Set up test environment"""
        plugin.Devices = fakeDomoticz.Devices
        plugin.Devices.clear()
        plugin.Domoticz = MagicMock()
    
    def tearDown(self):
        """Clean up"""
        plugin.Devices.clear()
    
    def test_update_device_nvalue_change(self):
        """Test UpdateDevice changes nValue when it differs"""
        # Create a test device
        test_device = fakeDomoticz.Device(Name="TestSwitch", Unit=1)
        test_device.Create()
        test_device.nValue = 0
        test_device.sValue = "Off"
        
        # Update with different nValue
        plugin.UpdateDevice(1, 1, "On")
        
        # Verify Update was called with new values
        self.assertEqual(plugin.Devices[1].nValue, 1)
        self.assertEqual(plugin.Devices[1].sValue, "On")
    
    def test_update_device_svalue_change(self):
        """Test UpdateDevice changes sValue when it differs"""
        # Create a test device
        test_device = fakeDomoticz.Device(Name="TestDimmer", Unit=2)
        test_device.Create()
        test_device.nValue = 0
        test_device.sValue = "0"
        
        # Update with different sValue
        plugin.UpdateDevice(2, 0, "50")
        
        # Verify Update was called
        self.assertEqual(plugin.Devices[2].sValue, "50")
    
    def test_update_device_no_change(self):
        """Test UpdateDevice does nothing when values haven't changed"""
        # Create a test device
        test_device = fakeDomoticz.Device(Name="TestDevice", Unit=3)
        test_device.Create()
        test_device.nValue = 1
        test_device.sValue = "On"
        test_device.Update = MagicMock()
        
        # Try to update with same values
        plugin.UpdateDevice(3, 1, "On")
        
        # Verify Update was NOT called since nothing changed
        test_device.Update.assert_not_called()
    
    def test_update_nonexistent_device(self):
        """Test UpdateDevice gracefully handles nonexistent device"""
        # Don't create any device with unit 999
        
        # This should not raise an exception
        try:
            plugin.UpdateDevice(999, 1, "On")
        except KeyError:
            self.fail("UpdateDevice should not raise KeyError for nonexistent device")
    
    def test_update_device_with_image(self):
        """Test UpdateDevice can update device with new image"""
        # Create a test device
        test_device = fakeDomoticz.Device(Name="TestDeviceWithImage", Unit=6)
        test_device.Create()
        test_device.nValue = 0
        test_device.sValue = "Off"
        
        # Mock an image
        fake_image = "fake_image.zip"
        fakeDomoticz.Image(fake_image)  # This will create an image in the fake environment
        
        # Update device with new image
        plugin.UpdateDevice(6, 0, "Off", Image=fake_image)
        
        # Verify the image was updated
        self.assertEqual(plugin.Devices[6].Image, fake_image)
        
    def test_update_device_with_multiple_changes(self):
        """Test UpdateDevice with nValue and sValue both changing"""
        # Create a test device
        test_device = fakeDomoticz.Device(Name="TestDimmer", Unit=4)
        test_device.Create()
        test_device.nValue = 0
        test_device.sValue = "0"
        
        # Update with different nValue and sValue
        plugin.UpdateDevice(4, 50, "50")
        
        # Verify both values changed
        self.assertEqual(plugin.Devices[4].nValue, 50)
        self.assertEqual(plugin.Devices[4].sValue, "50")
    
    def test_update_device_multiple_updates(self):
        """Test UpdateDevice can update the same device multiple times"""
        # Create a test device
        test_device = fakeDomoticz.Device(Name="TestDevice", Unit=5)
        test_device.Create()
        test_device.nValue = 0
        test_device.sValue = "Off"
        
        # First update
        plugin.UpdateDevice(5, 1, "On")
        self.assertEqual(plugin.Devices[5].nValue, 1)
        self.assertEqual(plugin.Devices[5].sValue, "On")
        
        # Second update to different values
        plugin.UpdateDevice(5, 2, "Half")
        self.assertEqual(plugin.Devices[5].nValue, 2)
        self.assertEqual(plugin.Devices[5].sValue, "Half")
        
        # Third update back to original
        plugin.UpdateDevice(5, 0, "Off")
        self.assertEqual(plugin.Devices[5].nValue, 0)
        self.assertEqual(plugin.Devices[5].sValue, "Off")
    
    def test_update_device_multiple_units(self):
        """Test UpdateDevice works with multiple different devices"""
        # Create multiple test devices
        device_1 = fakeDomoticz.Device(Name="Device1", Unit=10)
        device_1.Create()
        device_1.nValue = 0
        device_1.sValue = "Off"
        
        device_2 = fakeDomoticz.Device(Name="Device2", Unit=20)
        device_2.Create()
        device_2.nValue = 0
        device_2.sValue = "Off"
        
        # Update both devices with different values
        plugin.UpdateDevice(10, 1, "On")
        plugin.UpdateDevice(20, 2, "Half")
        
        # Verify each device has correct values
        self.assertEqual(plugin.Devices[10].nValue, 1)
        self.assertEqual(plugin.Devices[10].sValue, "On")
        self.assertEqual(plugin.Devices[20].nValue, 2)
        self.assertEqual(plugin.Devices[20].sValue, "Half")