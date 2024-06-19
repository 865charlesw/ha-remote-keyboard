from evdev import list_devices, InputDevice
import json
from main import CONFIG_PATH, get_devices


def main():
    devices = get_devices()
    device_lines = "\n".join(
        f"  {idx}: {device.name}" for idx, device in enumerate(devices)
    )
    print(f"Input Devices:\n{device_lines}")
    device_index = input(
        "Select an input device (if you don't see yours, try rebooting): "
    )
    webhook_id = input("Enter the webhook ID: ")
    repeat_delay_ms = input("Enter the repeat delay in ms (default 500): ")
    config = {
        "input_device_name": devices[int(device_index)],
        "webhook_id": webhook_id,
        "repeat_delay_ms": repeat_delay_ms or 500,
    }
    CONFIG_PATH.write_text(json.dumps(config, indent=4) + "\n")
    print(f"Configuration written to {CONFIG_PATH}")


if __name__ == "__main__":
    main()
