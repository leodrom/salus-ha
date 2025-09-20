from salus import Salus

# Create Salus object
s = Salus()

# Perform login
s.do_login(
    'dmitry.kosaryev@gmail.com',
    'supermarker'
)

# Extract security token
s.parse_token()
print(f"Security Token: {s.token}")

# Device ID (replace with your own)
device_id = "50361264"

# Get full JSON values for the device
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
