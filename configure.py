from evdev import list_devices, InputDevice
import json
from .main import CONFIG_PATH

DEVICE_DIR = "/dev/input"


def main():
    devices = [InputDevice(path).name for path in enumerate(list_devices(DEVICE_DIR))]
    device_lines = "\n".join(f"  {idx}: {name}" for idx, name in enumerate(devices))
    print(f"Input Devices:\n{device_lines}")
    device_index = input("Select an input device: ")
    webhook_id = input("Enter the webhook ID: ")
    repeat_delay_ms = input("Enter the repeat delay in ms (default 500): ")
    config = {
        "input_device_name": devices[int(device_index)],
        "webhook_id": webhook_id,
        "repeat_delay_ms": repeat_delay_ms or 500,
    }
    config = {
        "input_device_name": "INPUT_DEVICE_NAME",
        "repeat_delay_ms": 500,
        "webhook_id": "WEBHOOK_ID",
    }
    CONFIG_PATH.write_text(json.dumps(config, indent=4))
    print(f"Configuration written to {CONFIG_PATH}")


if __name__ == "__main__":
    main()
