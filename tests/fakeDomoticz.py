#
#   Very simple module to make local testing easier
#   It "emulates" Domoticz.Log() and Domoticz.Debug()
#
from typing import Any, Dict


Parameters: Dict[str, Any] = {"Mode1":None, 
                              "Mode2":None, 
                              "Mode3":None, 
                              "Mode4":None,
                              "Mode5":None,
                              "Mode6":"0"}
Images: Dict[str, Any] = {}
Devices: Dict[str, Any] = {}

class X:
    """
    fake class
    """
    ID:str = None
    Name:str = None
    Unit:str = None
    DeviceID = None
    sValue:str =  None
    Description :str = None
    level :int = None
    nValue: int = None
    LastLevel: int = None
    Image:str = None
    def __init__(self, aID:str, Name:str=None, DeviceID:str=None, Image:str=None, Unit:str=None, **kwargs) -> None:
        self.ID = aID
        self.Name = Name or str(aID)
        self.Unit = Unit or aID
        if DeviceID:
            self.DeviceID = DeviceID
        else:
            self.DeviceID = aID    
        self.sValue = str(aID)
        self.nValue = None
        self.Image = Image
        # Set any additional kwargs as attributes
        for k, v in kwargs.items():
            setattr(self, k, v)
        pass
    
    def Create(self):
        # Add to Devices
        Devices[self.Unit] = self
        pass


    def Update(self, 
               nValue:str,  
               sValue:str=None, 
               Name:str=None,
               alarmData:str=None, 
               Description:str=None,  
               Image=None):
        #self.level = alarmLevel
        if Name is not None:
            self.Name = Name
        if Description is not None:
            self.Description = Description
        self.nValue=nValue
        if sValue is not None:
            self.sValue=sValue
        if Image is not None:
            self.Image = Image
        pass

def Image(sZip:str):
    Debug("create image: "+sZip)
    img = X(sZip)
    # Map zip names to expected image keys
    key_map = {
        "uanyone.zip": "UnifiPresenceAnyone",
        "uoverride.zip": "UnifiPresenceOverride",
        "udevice.zip": "UnifiPresenceDevice"
    }
    id = key_map.get(sZip, sZip.replace(".zip",""))
    Images[id] = img
    return img


def Device(Name:str, Unit:str=None, TypeName:str=None, Used:bool=1, Switchtype:int=18, DeviceID:str=None, Options:str=None, **kwargs):
    x = X(Unit or Name, Name=Name, Unit=Unit, DeviceID=DeviceID, TypeName=TypeName, Used=Used, Switchtype=Switchtype, Options=Options, **kwargs)
    return x

def Log(s):
    print(s)


def Debug(s):
    print("Debug: {}".format(s))


def Error(s):
    print("Error: {}".format(s))

def Debugging(i):
    print("Debug: turned on")

def UpdateDevice(Unit, nValue, sValue, *args):
    if Unit in Devices:
        Devices[Unit].nValue = nValue
        Devices[Unit].sValue = sValue
        # Optionally, update LastUpdate if needed
        if hasattr(Devices[Unit], 'LastUpdate'):
            from datetime import datetime
            Devices[Unit].LastUpdate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')