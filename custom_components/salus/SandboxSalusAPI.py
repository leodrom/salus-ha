from SalusAPI import SalusAPI
from time import sleep

api = SalusAPI()
api.login("dmitry.kosaryev@gmail.com", "supermarker")

devices = api.fetch_devices()
for dev in devices:
    print(f"Device {dev.name} (id={dev.dev_id})")
    print(
        "  Summary -> mode: {mode}, online: {online}, room: {room}°C, setpoint: {set_point}°C, "
        "relay: {relay}, signal: {signal}".format(
            mode=dev.get_mode,
            online=dev.get_online_status,
            room=dev.get_room_temperature,
            set_point=dev.get_set_point_temperature,
            relay=dev.get_relay_active,
            signal=dev.get_signal_level,
        )
    )

# Device SRT00091527 (id=50361264)

dev = devices.find_by_name("SRT00091527")
if dev is None:
    print("Device SRT00091527 not found!")
else:
    dev.set_set_point_temperature(21.5)
    sleep(10)
    dev.turn_off()
    sleep(10)
    dev.turn_on()
    #dev.set_mode_manual()
    
    ## Manipulate device (uncomment to use)
    #dev.set_mode_manual()
    #dev.set_set_point_temperature(22.0)
    #dev.turn_off()
