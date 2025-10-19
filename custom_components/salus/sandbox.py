from dataclasses import asdict

from salus import Salus

# Device ID (replace with your own)
device_id = "50361264"

# Security tocken. We have add this tocken for debug pupose only
# You should get your own tocken by login
#security_token = "340707-689407562"
security_token = ''

# Create Salus object
s = Salus()

# Set security token (for debug purposes)
s.security_token = security_token

# If you don't have a valid tocken, you need to perform login
# and extract tocken from HTML response
if s.security_token == "":
    # Perform login
    s.do_login(
        'dmitry.kosaryev@gmail.com',
        'supermarker'
    )

    # Extract security token
    s.parse_token()
    print(f"Security Token: {s.security_token}")


# Get full JSON values for the device
# https://salus-it500.com/public/ajax_device_values.php?devId=50361264&token=340707-689407562&_=1758387578228
# https://salus-it500.com/public/ajax_device_values.php?devId=50361264&token=340707-1706367186&_=1758388154048
values = s.get_device_values(device_id)

# Use helper functions
mode = s.get_mode(values)
room_temp = s.get_room_temperature(values)
setpoint = s.get_setpoint(values)
flame = s.get_flame_status(values)
battery = s.get_battery_status(values)
signal = s.get_signal_level(values)

# Print results
print("Device values JSON:", values)
print(f"Mode: {mode}")
print(f"Room temperature: {room_temp} °C")
print(f"Setpoint temperature: {setpoint} °C")
print(f"Flame status: {'On' if flame else 'Off'}")
print(f"Battery status: {battery}")
print(f"Signal level: {signal}")
