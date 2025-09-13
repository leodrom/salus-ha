# Salus Library
# That library is used to communicate with Salus IT500 server
# It uses requests library to perform HTTP requests and HTMLParser to parse HTML responces
# It also uses dataclasses to define a simple Device class to store device information
# We need to process login just to get security tocken
# Each device has its own ID that should be used to get device information and to set temperature
# The security token is requested for each operation

from dataclasses import dataclass
import requests
from html.parser import HTMLParser

# Salus Device Class
@dataclass
class Device:
    id: str = ''
    code: str = ''
    name: str = ''
    online: bool = False  # device online status
    current_temperature: float = 0.0
    target_temperature: float = 0.0
    status: str = 'off'  # on or off

# Salus Class responsible for communication with Salus server        
class Salus:
    def __init__(self):
        # Create a new session object that will keep the cookies
        self.session = requests.Session()
        # Responce object contain last responce from server
        self.response = requests.Response()
        # After login server generates token that sshould be used in some requests
        self.token = ''


    # parse_page_name Check selft.responce object and try to read page title.
    # Each page has a title that we could use as a marker that we could use for the page type detection.
    # iT500 Login / Register - login page return 'login' if login page is detected
    # Your Devices - device list page return 'devices' if devices page is detected
    # T500 Control Panel - device control page return 'control' if control page is detected
    # return '' if we could not detect page type
    def parse_page_name(self):
        class TitleParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.title = ''
                self.is_title = False

            def handle_starttag(self, tag, attrs):
                if tag == 'title':
                    self.is_title = True

            def handle_data(self, data):
                if self.is_title:
                    self.title = data.strip()
                    self.is_title = False

        parser = TitleParser()
        parser.feed(self.response.text)
        title = parser.title

        if 'iT500 Login / Register' in title:
            return 'login'
        elif 'Your Devices' in title:
            return 'devices'
        elif 'T500 Control Panel' in title:
            return 'control'
        else:
            return ''


    # Devices page contains security token that should be used in some requests
    # This function parses the token from the devices page
    '''
    <input id="token" name="token" type="hidden" value="340707-69209650" />
    '''
    def parse_token(self):
        class TokenParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.token = ''
                self.is_token = False

            def handle_starttag(self, tag, attrs):
                if tag == 'input':
                    token_found = False
                    for attr in attrs:
                        if attr[0] == 'id' and attr[1] == 'token':
                            token_found = True
                        if token_found and attr[0] == 'value':
                            self.token = attr[1]
                            self.is_token = True

        parser = TokenParser()
        parser.feed(self.response.text)
        self.token = parser.token
        return self.token

    # Parse the devices page and return a list of devices
    def parse_devices_page(self):
        # HTML Parser for Devices Page
        # https://salus-it500.com/public/devices.php
        '''
        <div class="deviceList 201472051">
            <a class="deviceIcon online " href="control.php?devId=201472051">SRT00031984 Parkova 12</a>
            <span class="renameDevice_icon" onclick="Toggle('201472051');">RENAME</span>
            <form class="renameForm" action="../includes/rename.php" method="post" name="201472051" id="201472051">
                <input class="devicePageInputs" name="name" type="text" onclick="select()" placeholder="New Device Name" size="16" maxlength="11" /> 
                <input name="devId" type="hidden" value="201472051"/>
                <input name="submitRename" type="submit" value="submit" />
            </form>
            <a class="removeDevice" onclick="return confirm('Are you sure you want to remove this device?')" href="../includes/remove_device.php?devId=201472051">remove</a>
        </div>
        '''
        class DeviceParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.devices = []
                    self.current_device_status = ''
                    self.is_device = False

                def handle_starttag(self, tag, attrs):
                    if tag == 'a':
                        for attr in attrs:
                            if attr[0] == 'href' and 'control.php?devId' in attr[1]:
                                self.is_device = True
                                self.current_device = Device(id=attr[1].split('=')[1], code='', name='', online=False, current_temperature=0.0, target_temperature=0.0, status='')
                            if attr[0] == 'class' and 'deviceIcon' in attr[1]:
                                self.current_device_status = 'online' if 'online' in attr[1] else 'offline'
                                
                def handle_data(self, data):
                    if self.is_device:
                        parts = data.strip().split(' ', 1)
                        
                        self.current_device.code = parts[0]
                        self.current_device.name = ' '.join(parts[1:]) if len(parts) > 1 else ''
                        self.current_device.online = self.current_device_status == 'online'
                        
                        self.devices.append(self.current_device)
                        self.current_device = None
                        self.current_device_status = ''
                        self.is_device = False

        parser = DeviceParser()
        parser.feed(self.response.text)
        return parser.devices

    # Try to login on https://salus-it500.com/public/login.php page.
    # that function does not perform successfull login check
    # its return responce object that could contains device list or login error 
    def do_login(self, username='', password=''):
        url = 'https://salus-it500.com/public/login.php'
        data = {
            'IDemail': username,
            'password': password,
            'login': 'Login'
        }
        self.response = self.session.post(url, data=data)
        return self.response

    def check_device_battery(self, device_id):
        url = 'https://salus-it500.com/ota/battery_check.php'  # Adjust the URL as per your server
        params = {'devId': device_id}
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()  # Raise an exception for HTTP errors
            battery_data = response.json()  # Assuming the response is in JSON format
            return battery_data
        except requests.exceptions.RequestException as e:
            print(f"Error while checking battery: {e}")
            return None
        
    # Check login responce status. that function checks responce after login and try to find the block with error message
    # if block with error message is deteted that function returns False. Otherwise returns True.
    # <p class="errorMessage">Invalid login name or password<br></p>
    # in case of error message is detected that function saves error message in self.error_message
    def check_login_error_status(self):
        class LoginErrorParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.error_message = ''
                self.is_error_message = False;
                         
            def handle_starttag(self, tag, attrs):
                if tag == 'p':
                    for attr in attrs:
                        if attr[0] == 'class' and 'errorMessage' in attr[1]:
                            self.error_message = ''
                            self.is_error_message = True

            def handle_data(self, data):
                if self.is_error_message:
                    self.error_message = data.strip()
                    self.is_error_message = False

        parser = LoginErrorParser()
        parser.feed(self.response.text )
        self.error_message = parser.error_message
        return self.error_message == ''
    # get_device_info - get device info by device id. That function performs request to the server and returns device info
    # The request is looks like https://salus-it500.com/public/ajax_device_values.php?devId=50361264&token=340707-69209650
    # For that call we need to have: device_id as function parameter and sel.token as a security token.
    
    # JSON responce exmaple:
    '''
    {"CH1currentRoomTemp":"32.0","CH1currentSetPoint":"32.0","CH1autoOff":"","CH1manual":"","CH1schedType":"","CH1heatOnOffStatus":"","CH1autoMode":"","CH1heatOnOff":"","CH1frostActive":"","CH2currentRoomTemp":"32.0","CH2currentSetPoint":"32.0","CH2autoOff":"","CH2manual":"","CH2schedType":"","CH2heatOnOffStatus":"","CH2autoMode":"","CH2heatOnOff":"","CH2frostActive":"","HWmode":"","HWboost":"","HWschedType":"","HWonOffStatus":"","HWautoMode":"","esStatus":"","tempUnit":"","timeFormat":"","holidayoption":"","holidayStatus":"expired","holiday_start":"01-01-1970 12:00 am","holiday_finish":"01-01-1970 12:00 am","z1pMon":{"z1pMon1Time":"12:00 am","z1pMon1Temp":"0.0 \u00b0C","z1pMon2Time":"12:00 am","z1pMon2Temp":"0.0 \u00b0C","z1pMon3Time":"12:00 am","z1pMon3Temp":"0.0 \u00b0C","z1pMon4Time":"12:00 am","z1pMon4Temp":"0.0 \u00b0C","z1pMon5Time":"12:00 am","z1pMon5Temp":"0.0 \u00b0C","z1pMon6Time":"12:00 am","z1pMon6Temp":"0.0 \u00b0C"},"z1pTus":{"z1pTus1Time":"12:00 am","z1pTus1Temp":"0.0 \u00b0C","z1pTus2Time":"12:00 am","z1pTus2Temp":"0.0 \u00b0C","z1pTus3Time":"12:00 am","z1pTus3Temp":"0.0 \u00b0C","z1pTus4Time":"12:00 am","z1pTus4Temp":"0.0 \u00b0C","z1pTus5Time":"12:00 am","z1pTus5Temp":"0.0 \u00b0C","z1pTus6Time":"12:00 am","z1pTus6Temp":"0.0 \u00b0C"},"z1pWed":{"z1pWed1Time":"12:00 am","z1pWed1Temp":"0.0 \u00b0C","z1pWed2Time":"12:00 am","z1pWed2Temp":"0.0 \u00b0C","z1pWed3Time":"12:00 am","z1pWed3Temp":"0.0 \u00b0C","z1pWed4Time":"12:00 am","z1pWed4Temp":"0.0 \u00b0C","z1pWed5Time":"12:00 am","z1pWed5Temp":"0.0 \u00b0C","z1pWed6Time":"12:00 am","z1pWed6Temp":"0.0 \u00b0C"},"z1pThu":{"z1pThu1Time":"12:00 am","z1pThu1Temp":"0.0 \u00b0C","z1pThu2Time":"12:00 am","z1pThu2Temp":"0.0 \u00b0C","z1pThu3Time":"12:00 am","z1pThu3Temp":"0.0 \u00b0C","z1pThu4Time":"12:00 am","z1pThu4Temp":"0.0 \u00b0C","z1pThu5Time":"12:00 am","z1pThu5Temp":"0.0 \u00b0C","z1pThu6Time":"12:00 am","z1pThu6Temp":"0.0 \u00b0C"},"z1pFri":{"z1pFri1Time":"12:00 am","z1pFri1Temp":"0.0 \u00b0C","z1pFri2Time":"12:00 am","z1pFri2Temp":"0.0 \u00b0C","z1pFri3Time":"12:00 am","z1pFri3Temp":"0.0 \u00b0C","z1pFri4Time":"12:00 am","z1pFri4Temp":"0.0 \u00b0C","z1pFri5Time":"12:00 am","z1pFri5Temp":"0.0 \u00b0C","z1pFri6Time":"12:00 am","z1pFri6Temp":"0.0 \u00b0C"},"z1pSat":{"z1pSat1Time":"12:00 am","z1pSat1Temp":"0.0 \u00b0C","z1pSat2Time":"12:00 am","z1pSat2Temp":"0.0 \u00b0C","z1pSat3Time":"12:00 am","z1pSat3Temp":"0.0 \u00b0C","z1pSat4Time":"12:00 am","z1pSat4Temp":"0.0 \u00b0C","z1pSat5Time":"12:00 am","z1pSat5Temp":"0.0 \u00b0C","z1pSat6Time":"12:00 am","z1pSat6Temp":"0.0 \u00b0C"},"z1pSun":{"z1pSun1Time":"12:00 am","z1pSun1Temp":"0.0 \u00b0C","z1pSun2Time":"12:00 am","z1pSun2Temp":"0.0 \u00b0C","z1pSun3Time":"12:00 am","z1pSun3Temp":"0.0 \u00b0C","z1pSun4Time":"12:00 am","z1pSun4Temp":"0.0 \u00b0C","z1pSun5Time":"12:00 am","z1pSun5Temp":"0.0 \u00b0C","z1pSun6Time":"12:00 am","z1pSun6Temp":"0.0 \u00b0C"},"z2pMon":{"z2pMon1Time":"12:00 am","z2pMon1Temp":"0.0 \u00b0C","z2pMon2Time":"12:00 am","z2pMon2Temp":"0.0 \u00b0C","z2pMon3Time":"12:00 am","z2pMon3Temp":"0.0 \u00b0C","z2pMon4Time":"12:00 am","z2pMon4Temp":"0.0 \u00b0C","z2pMon5Time":"12:00 am","z2pMon5Temp":"0.0 \u00b0C","z2pMon6Time":"12:00 am","z2pMon6Temp":"0.0 \u00b0C"},"z2pTus":{"z2pTus1Time":"12:00 am","z2pTus1Temp":"0.0 \u00b0C","z2pTus2Time":"12:00 am","z2pTus2Temp":"0.0 \u00b0C","z2pTus3Time":"12:00 am","z2pTus3Temp":"0.0 \u00b0C","z2pTus4Time":"12:00 am","z2pTus4Temp":"0.0 \u00b0C","z2pTus5Time":"12:00 am","z2pTus5Temp":"0.0 \u00b0C","z2pTus6Time":"12:00 am","z2pTus6Temp":"0.0 \u00b0C"},"z2pWed":{"z2pWed1Time":"12:00 am","z2pWed1Temp":"0.0 \u00b0C","z2pWed2Time":"12:00 am","z2pWed2Temp":"0.0 \u00b0C","z2pWed3Time":"12:00 am","z2pWed3Temp":"0.0 \u00b0C","z2pWed4Time":"12:00 am","z2pWed4Temp":"0.0 \u00b0C","z2pWed5Time":"12:00 am","z2pWed5Temp":"0.0 \u00b0C","z2pWed6Time":"12:00 am","z2pWed6Temp":"0.0 \u00b0C"},"z2pThu":{"z2pThu1Time":"12:00 am","z2pThu1Temp":"0.0 \u00b0C","z2pThu2Time":"12:00 am","z2pThu2Temp":"0.0 \u00b0C","z2pThu3Time":"12:00 am","z2pThu3Temp":"0.0 \u00b0C","z2pThu4Time":"12:00 am","z2pThu4Temp":"0.0 \u00b0C","z2pThu5Time":"12:00 am","z2pThu5Temp":"0.0 \u00b0C","z2pThu6Time":"12:00 am","z2pThu6Temp":"0.0 \u00b0C"},"z2pFri":{"z2pFri1Time":"12:00 am","z2pFri1Temp":"0.0 \u00b0C","z2pFri2Time":"12:00 am","z2pFri2Temp":"0.0 \u00b0C","z2pFri3Time":"12:00 am","z2pFri3Temp":"0.0 \u00b0C","z2pFri4Time":"12:00 am","z2pFri4Temp":"0.0 \u00b0C","z2pFri5Time":"12:00 am","z2pFri5Temp":"0.0 \u00b0C","z2pFri6Time":"12:00 am","z2pFri6Temp":"0.0 \u00b0C"},"z2pSat":{"z2pSat1Time":"12:00 am","z2pSat1Temp":"0.0 \u00b0C","z2pSat2Time":"12:00 am","z2pSat2Temp":"0.0 \u00b0C","z2pSat3Time":"12:00 am","z2pSat3Temp":"0.0 \u00b0C","z2pSat4Time":"12:00 am","z2pSat4Temp":"0.0 \u00b0C","z2pSat5Time":"12:00 am","z2pSat5Temp":"0.0 \u00b0C","z2pSat6Time":"12:00 am","z2pSat6Temp":"0.0 \u00b0C"},"z2pSun":{"z2pSun1Time":"12:00 am","z2pSun1Temp":"0.0 \u00b0C","z2pSun2Time":"12:00 am","z2pSun2Temp":"0.0 \u00b0C","z2pSun3Time":"12:00 am","z2pSun3Temp":"0.0 \u00b0C","z2pSun4Time":"12:00 am","z2pSun4Temp":"0.0 \u00b0C","z2pSun5Time":"12:00 am","z2pSun5Temp":"0.0 \u00b0C","z2pSun6Time":"12:00 am","z2pSun6Temp":"0.0 \u00b0C"},"hwMon":{"hwMon1ontime":"12:00 am","hwMon1offtime":"12:00 am","hwMon2ontime":"12:00 am","hwMon2offtime":"12:00 am","hwMon3ontime":"12:00 am","hwMon3offtime":"12:00 am"},"hwTus":{"hwTus1ontime":"12:00 am","hwTus1offtime":"12:00 am","hwTus2ontime":"12:00 am","hwTus2offtime":"12:00 am","hwTus3ontime":"12:00 am","hwTus3offtime":"12:00 am"},"hwWed":{"hwWed1ontime":"12:00 am","hwWed1offtime":"12:00 am","hwWed2ontime":"12:00 am","hwWed2offtime":"12:00 am","hwWed3ontime":"12:00 am","hwWed3offtime":"12:00 am"},"hwThu":{"hwThu1ontime":"12:00 am","hwThu1offtime":"12:00 am","hwThu2ontime":"12:00 am","hwThu2offtime":"12:00 am","hwThu3ontime":"12:00 am","hwThu3offtime":"12:00 am"},"hwFri":{"hwFri1ontime":"12:00 am","hwFri1offtime":"12:00 am","hwFri2ontime":"12:00 am","hwFri2offtime":"12:00 am","hwFri3ontime":"12:00 am","hwFri3offtime":"12:00 am"},"hwSat":{"hwSat1ontime":"12:00 am","hwSat1offtime":"12:00 am","hwSat2ontime":"12:00 am","hwSat2offtime":"12:00 am","hwSat3ontime":"12:00 am","hwSat3offtime":"12:00 am"},"hwSun":{"hwSun1ontime":"12:00 am","hwSun1offtime":"12:00 am","hwSun2ontime":"12:00 am","hwSun2offtime":"12:00 am","hwSun3ontime":"12:00 am","hwSun3offtime":"12:00 am"},"frost":"32"}
    '''
    
    #https://salus-it500.com/public/ajax_device_values.php?devId=50361264&token=340707-2078146864
    #https://salus-it500.com/public/ajax_device_values.php?devId=201472051&token=340707-2078146864
    def get_device_info(self, device_id):
        # Compose the URL for the device info request
        url = f'https://salus-it500.com/public/ajax_device_values.php?devId={device_id}&token={self.token}'
        print(f"Device Info URL: {url}")
        
        response = self.session.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        device_info = response.json()  # Assuming the response is in JSON format

        # Parse the device information
        contactable = not (device_info['CH1currentSetPoint'] == 32.0) #Temperature that is equals to 32 means that device in not contactable
        current_temperature = float(device_info['CH1currentRoomTemp'])
        target_temperature = float(device_info['CH1currentSetPoint'])
        status = 'on' if device_info['CH1heatOnOffStatus'] == 1 else 'off'

        result = Device()
        result.id = device_id
        result.code = device_info.get('deviceCode', '')
        result.name = device_info.get('deviceName', '')
        result.online = contactable
        result.current_temperature = current_temperature
        result.target_temperature = target_temperature
        result.status = status
        return result
    
    # Set the temperature for the device
    def set_temperature(self, dev_id, temperature):
        url = "https://salus-it500.com/includes/set.php"
        payload = {
            'token': self.token,
            'tempUnit': 0,  # Celsius
            'devId': dev_id,
            'current_tempZ1_set': 1,  # Set temperature flag
            'current_tempZ1': round(temperature, 1)  # Temperature to set
        }
        response = requests.post(url, data=payload)
        return response
