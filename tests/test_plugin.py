from unittest import TestCase

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
        
    def test_onStart(self):
        self.plugin.onStart()
        
    def test_setVersionCheck(self):
        self.plugin.setVersionCheck(None, None)
        
        self.plugin.setVersionCheck(True, None)
        
        self.plugin.setVersionCheck(False, None)
