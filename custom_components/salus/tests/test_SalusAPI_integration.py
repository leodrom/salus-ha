import importlib.util
import pathlib
import unittest
from typing import Optional

try:
    import requests
    from requests.exceptions import HTTPError
except ModuleNotFoundError as exc:  # pragma: no cover - skip if requests missing
    requests = None
    HTTPError = RuntimeError
    REQUESTS_IMPORT_ERROR = exc
else:
    REQUESTS_IMPORT_ERROR = None

MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "SalusAPI.py"

SalusAPI = None
InvalidCredentialsError = RuntimeError
SalusAPIError = RuntimeError
SalusDevice = None
DeviceCollection = None
Attributes = None
IMPORT_ERROR: Optional[Exception] = None

if MODULE_PATH.exists():
    spec = importlib.util.spec_from_file_location("SalusAPI", MODULE_PATH)
    SalusModule = importlib.util.module_from_spec(spec) if spec and spec.loader else None
    if spec and spec.loader and SalusModule is not None:
        try:
            spec.loader.exec_module(SalusModule)  # type: ignore[arg-type]
            SalusAPI = getattr(SalusModule, "SalusAPI", None)
            InvalidCredentialsError = getattr(SalusModule, "InvalidCredentialsError", RuntimeError)
            SalusAPIError = getattr(SalusModule, "SalusAPIError", RuntimeError)
            SalusDevice = getattr(SalusModule, "SalusDevice", None)
            DeviceCollection = getattr(SalusModule, "DeviceCollection", None)
            Attributes = getattr(SalusModule, "Attributes", None)
        except Exception as exc:  # pragma: no cover - capture load errors
            IMPORT_ERROR = exc
    else:  # pragma: no cover - spec creation failed
        IMPORT_ERROR = RuntimeError("Unable to load SalusAPI module")
else:  # pragma: no cover - missing file
    IMPORT_ERROR = FileNotFoundError(MODULE_PATH)


USERNAME = "dmitry.kosaryev@gmail.com"
PASSWORD_OK = "supermarker"
PASSWORD_BAD = "supermarker-invalid"


@unittest.skipIf(requests is None, f"requests unavailable: {REQUESTS_IMPORT_ERROR}")
class TestSalusAPIIntegration(unittest.TestCase):
    @unittest.skipIf(SalusAPI is None, f"SalusAPI unavailable: {IMPORT_ERROR}")
    def test_login_success(self):
        api = SalusAPI()
        api.login(USERNAME, PASSWORD_OK)

        self.assertTrue(api.user_id)
        self.assertTrue(api.sec_token)

    @unittest.skipIf(SalusAPI is None, f"SalusAPI unavailable: {IMPORT_ERROR}")
    def test_login_failure(self):
        api = SalusAPI()
        with self.assertRaises(InvalidCredentialsError) as ctx:
            api.login(USERNAME, PASSWORD_BAD)

        self.assertIn("Invalid login name or password", str(ctx.exception))

    @unittest.skipIf(
        SalusAPI is None or SalusDevice is None or DeviceCollection is None or Attributes is None,
        f"SalusAPI unavailable: {IMPORT_ERROR}",
    )
    def test_fetch_devices(self):
        api = SalusAPI()
        api.login(USERNAME, PASSWORD_OK)

        devices = api.fetch_devices()

        self.assertIsInstance(devices, DeviceCollection)
        for device in devices:
            self.assertIsInstance(device, SalusDevice)
            self.assertTrue(device.dev_id)

    @unittest.skipIf(
        SalusAPI is None or SalusDevice is None or DeviceCollection is None or Attributes is None,
        f"SalusAPI unavailable: {IMPORT_ERROR}",
    )
    def test_fetch_device_attributes(self):
        api = SalusAPI()
        api.login(USERNAME, PASSWORD_OK)

        devices = api.fetch_devices()
        self.assertIsInstance(devices, DeviceCollection)
        self.assertGreater(len(devices), 0)

        for device in devices:
            attrs = device.fetch_attributes()
            self.assertIsInstance(attrs, Attributes)
            self.assertGreater(len(attrs), 0, f"No attributes returned for device {device.dev_id}")

    @unittest.skipIf(
        SalusAPI is None or SalusDevice is None or DeviceCollection is None or Attributes is None,
        f"SalusAPI unavailable: {IMPORT_ERROR}",
    )
    def test_fetch_attributes_invalid_device(self):
        api = SalusAPI()
        api.login(USERNAME, PASSWORD_OK)

        devices = api.fetch_devices()
        self.assertIsInstance(devices, DeviceCollection)
        self.assertGreater(len(devices), 0)

        device_type_id = devices[0].device_type_id

        with self.assertRaises(SalusAPIError):
            api.get_attributes("invalid-device-id", device_type_id)

TEST_ORDER = [
    "test_login_failure",
    "test_login_success",
    "test_fetch_devices",
    "test_fetch_device_attributes",
    "test_fetch_attributes_invalid_device",
]


class OrderedLoader(unittest.TestLoader):
    def sortTestMethodsUsing(self, a, b):
        order_map = {name: index for index, name in enumerate(TEST_ORDER)}
        return order_map.get(a, len(order_map)) - order_map.get(b, len(order_map))


if __name__ == "__main__":
    unittest.main(exit=True, verbosity=2, testLoader=OrderedLoader())
