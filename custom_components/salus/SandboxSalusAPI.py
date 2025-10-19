from SalusAPI import SalusAPI

api = SalusAPI()
api.login("dmitry.kosaryev@gmail.com", "supermarker")

devices = api.fetch_devices()
for dev in devices:
    print(f"Device {dev.name} (id={dev.dev_id})")
    print(
        "  Summary -> mode: {mode}, online: {online}, room: {room}°C, setpoint: {set_point}°C, "
        "relay: {relay}, signal: {signal}".format(
            mode=dev.mode,
            online=dev.online_status,
            room=dev.room_temperature,
            set_point=dev.set_point,
            relay=dev.relay_active,
            signal=dev.signal_level,
        )
    )


# Device SRT00091527 (id=50361264)
#TODO: I have device list devices. I need to get device by id (SRT00091527)

    ## Manipulate device (uncomment to use)
    #dev.set_mode_manual()
    #dev.set_temperature(22.0)
    #dev.turn_off()
