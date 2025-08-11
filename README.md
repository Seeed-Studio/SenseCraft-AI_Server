# SenseCraft-AI_Server

[English](README.md) | [中文](README_CN.md)

Run AI Task on your Edge Device.

## Introduction

The Server running on your edge device, handling input and output, enabling model switching, offering output streaming after inference, and parameter configuration.

## Features

- Auto-handling different input sources, such as MP4, IP cameras, and USB cameras.
- Dynamically switching AI models, currently supporting YOLOv8, but easily expandable.
- Simple and user-friendly MJPEG streaming output, accessible with just a browser, even on your phone.
- Publishes recognition results through MQTT, easily adaptable to your requirements.

## Usage Example

**Remind:** `Jetson orin nano 4G` can barely run, please try not to run other programs at the same time.

The easiest way is to run it using Docker. If you prefer running the source code directly on your local machine, please refer to the [Advanced Usage](#advanced-usage).

```sh
# make sure Docker installed, and run the Edge in container
bash scripts/run.sh

# The script will automatically:
# 1. Check and build Docker image (if needed)
# 2. Check MQTT service status
# 3. Start SenseCraft AI Server

# Access the web interface
# in machine 
http://localhost:46654/
# in other machine
http://machine-ip:46654/
```

### MQTT Service Management
```sh
# Check MQTT service status
./scripts/mqtt.sh status

# Start MQTT service
./scripts/mqtt.sh start

# Install MQTT service (if not installed)
./scripts/mqtt.sh install
```

### Environment Check
```sh
# Check runtime environment (without starting service)
./scripts/test-run.sh

# View all available scripts
ls -la scripts/
```

## Advanced Usage

- if you want run with python in host, check [Run In Host](docs/run-in-host.md)
- more details about Docker, check [Run with Docker](docs/run-with-docker.md)
- the web interface provides all features, check [Web UI](docs/web-ui.md)
- the output of inference working with MQTT, check [MQTT Output](docs/mqtt-output.md)
- add your models, check [Design #models](docs/design.md#models)
- add your source or upload source, check [Design #input](docs/design.md#input)
- file upload and management features, check [Upload Features](docs/UPLOAD_FEATURES.md)

## Project Structure

```
SenseCraft-AI_Server/
├── src/                    # Source code
├── dist/                   # Web interface files
├── docs/                   # Documentation
├── tests/                  # Test files and demos
├── scripts/                # Shell scripts
├── models/                 # AI models directory
├── sources/                # Video sources directory
├── configs/                # Configuration files
└── README.md              # This file
```

## Testing

- MQTT tests: [tests/README.md](tests/README.md)
- All documentation: [docs/README.md](docs/README.md)

## License

This project is released under the [MIT license](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for more information.

## History

See [CHANGELOG.md](CHANGELOG.md).
