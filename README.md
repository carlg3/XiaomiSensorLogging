# XiaomiSensorLogging

This is a simple project to read and log temperature and humidity data from a LYWSD03MMC with [ATC1441 custom firmware](https://github.com/atc1441/ATC_MiThermometer).

The code uses the [bleak library](https://pypi.org/project/bleak/) instead of [PyBluez](https://pybluez.readthedocs.io/en/latest/index.html) or [bluepy](https://pypi.org/project/bluepy/)
which where not compatible with my setup.
