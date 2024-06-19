import logging
from evdev import list_devices, InputDevice, categorize, ecodes, InputEvent, KeyEvent
import requests
import socket
import json
from pathlib import Path

WEBHOOK_BASE_URL = "https://www.mrcolfax.com/api/webhook"
LOG_LEVEL = logging.INFO
CONFIG_PATH = Path(__file__).parent / "config.json"


def main():
    # Setup Constants
    config = json.loads(CONFIG_PATH.read_text())
    global LOGGER, HOSTNAME, REPEAT_DELAY_SEC, WEBHOOK_URL
    LOGGER = logging.getLogger(__name__)
    HOSTNAME = socket.gethostname()
    REPEAT_DELAY_SEC = config["repeat_delay_ms"] / 1000
    WEBHOOK_URL = f"{WEBHOOK_BASE_URL}/{config['webhook_id']}"

    # Setup Logging
    logging.basicConfig()
    LOGGER.setLevel(LOG_LEVEL)

    # Get Input Device
    device: InputDevice = _get_device(config["input_device_name"])

    # Send Events
    with device.grab_context():
        _send_events(device)


def _get_device(device_name):
    available = get_devices()
    for device in available:
        if device.name == device_name:
            LOGGER.info(f"Found {device}")
            return device
    device_names = [device.name for device in available]
    raise Exception(f"Keyboard '{device_name}' not found in {device_names}")


def get_devices():
    return [InputDevice(path) for path in list_devices()]


def _send_events(device: InputDevice):
    handlers: dict[str, KeyHandler] = {}
    for event in device.read_loop():
        event: InputEvent
        if event.type != ecodes.EV_KEY:
            continue
        key_event: KeyEvent = categorize(event)
        keycode = key_event.keycode
        if isinstance(key_event.keycode, list):
            keycode = ",".join(keycode)
        if keycode not in handlers:
            handlers[keycode] = KeyHandler(keycode)
        handlers[keycode].handle(key_event)


class KeyHandler:
    def __init__(self, keycode: str):
        self.keycode = keycode
        self.holding = False
        self.presses: list[float] = []
        self.metadata = {"hostname": HOSTNAME, "keycode": self.keycode}

    def handle(self, key_event: KeyEvent):
        LOGGER.debug(f"Handling {key_event}")
        timestamp = key_event.event.timestamp()
        if key_event.keystate == KeyEvent.key_down:
            self.presses.append(timestamp)
            return
        last_down = self.presses[-1]
        if key_event.keystate == KeyEvent.key_hold:
            if not self.holding:
                self.holding = True
                self._send()
            return
        if key_event.keystate != KeyEvent.key_up:
            LOGGER.warning(
                f"Key {self.keycode} in unknown keystate {key_event.keystate}"
            )
            return
        if self.holding:
            self.holding = False
            self._send(timestamp - last_down)
            return
        cutoff = last_down - REPEAT_DELAY_SEC
        self.presses = [press for press in self.presses if press >= cutoff]
        self._send()

    def _send(self, hold_sec: int = None):
        data = self.metadata.copy()
        data["timestamp"] = self.presses[-1]
        data["details"] = {}
        if self.holding:
            data["action"] = "hold"
        elif hold_sec is not None:
            data["action"] = "release"
            data["details"]["hold_duration_ms"] = round(hold_sec * 1000)
        else:
            data["action"] = "press"
            data["details"]["count"] = len(self.presses)
        LOGGER.info(f"Sending {data}")
        response = requests.post(WEBHOOK_URL, json=data)
        response.raise_for_status()


if __name__ == "__main__":
    main()
