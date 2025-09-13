# Salus Home Assistant Integration

This custom integration provides a dummy Salus thermostat for Home Assistant. It exposes:

- Room temperature sensor (returns a constant value of 23°C)
- Target temperature sensor
- Thermostat entity with `heat` and `off` modes

The integration does not communicate with any real devices and is intended as a starting point for further development.

## Installation

1. Add this repository to HACS as a custom repository.
2. Install the **Salus** integration from HACS.
3. Add the integration to your `configuration.yaml` with credentials and restart Home Assistant:

   ```yaml
   salus:
     username: YOUR_USERNAME
     password: YOUR_PASSWORD
   ```

## Debug Logging

To enable debug logging for this integration, add the following to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.salus: debug
```

