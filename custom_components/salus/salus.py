# Salus Library
# That library is used to communicate with Salus IT500 server
# It uses requests library to perform HTTP requests and HTMLParser to parse HTML responces
# It also uses dataclasses to define a simple Device class to store device information
# We need to process login just to get security tocken
# Each device has its own ID that should be used to get device information and to set temperature
# The security token is requested for each operation

from dataclasses import dataclass
import logging
import requests
import time
import random
from html.parser import HTMLParser

_LOGGER = logging.getLogger(__name__)

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


# Salus Class responsible for communication with Salus IT500 server
class Salus:
    def __init__(self):
        # Session object keeps cookies across requests
        self.session = requests.Session()
        # Last HTTP response
        self.response = requests.Response()
        # Security token returned after login
        self.token = ''

    # Parse the <title> from HTML response and detect page type
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

    # Extract token value from HTML <input id="token" value="..."/>
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

    # Parse devices list page and extract devices
    def parse_devices_page(self):
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
                            self.current_device = Device(
                                id=attr[1].split('=')[1],
                                code='',
                                name='',
                                online=False,
                                current_temperature=0.0,
                                target_temperature=0.0,
                                status=''
                            )
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

    # Perform login to https://salus-it500.com/public/login.php
    def do_login(self, username='', password=''):
        url = 'https://salus-it500.com/public/login.php'
        data = {
            'IDemail': username,
            'password': password,
            'login': 'Login'
        }
        self.response = self.session.post(url, data=data)
        return self.response

    # Check login error message in response HTML
    def check_login_error_status(self):
        class LoginErrorParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.error_message = ''
                self.is_error_message = False

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
        parser.feed(self.response.text)
        self.error_message = parser.error_message
        return self.error_message == ''

    # Get device values JSON from ajax_device_values.php
    def get_device_values(self, device_id: str):
        """
        Fetch full JSON state for a device.
        The &_= parameter is generated as current timestamp.
        """
        timestamp = int(time.time() * 1000)
        url = (
            f"https://salus-it500.com/public/ajax_device_values.php"
            f"?devId={device_id}&token={self.token}&_={timestamp}"
        )
        _LOGGER.debug("Requesting device values: %s", url)
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    # --- Helper functions to extract values from JSON ---

    def get_mode(self, values: dict) -> str:
        """Return current operating mode: Off, Manual, Auto."""
        if values.get("CH1autoOff") == "1":
            return "Off"
        elif values.get("CH1manual") == "1":
            return "Manual"
        elif values.get("CH1autoMode") == "1":
            return "Auto"
        else:
            return "Unknown"

    def get_room_temperature(self, values: dict) -> float:
        """Return current room temperature."""
        return float(values.get("CH1currentRoomTemp", 0.0))

    def get_setpoint(self, values: dict) -> float:
        """Return current set temperature (setpoint)."""
        return float(values.get("CH1currentSetPoint", 0.0))

    def get_flame_status(self, values: dict) -> bool:
        """Return True if heating flame is on, False otherwise."""
        return values.get("CH1heatOnOff") == "1" or values.get("CH1heatOnOffStatus") == "1"

    def get_battery_status(self, values: dict) -> str:
        """Return battery status if available."""
        return values.get("batteryStatus", "unknown")

    def get_signal_level(self, values: dict) -> str:
        """Return signal level if available."""
        return values.get("signal", values.get("signalLevel", "unknown"))

    # Set target temperature
    def set_temperature(self, dev_id, temperature):
        url = "https://salus-it500.com/includes/set.php"
        payload = {
            'token': self.token,
            'tempUnit': 0,  # Celsius
            'devId': dev_id,
            'current_tempZ1_set': 1,
            'current_tempZ1': round(temperature, 1)
        }
        response = requests.post(url, data=payload)
        return response

    # Set the HVAC mode (on/off) for the device
    def set_hvac_mode(self, dev_id, hvac_mode):
        url = "https://salus-it500.com/includes/set.php"
        payload = {
            'token': self.token,
            'devId': dev_id,
        }

        # Salus API expects 1 for on (heat) and 0 for off
        payload['power'] = 1 if str(hvac_mode).lower() != 'off' else 0

        response = requests.post(url, data=payload)
        return response
