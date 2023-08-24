# SenseCraft-AI-Edge

Run AI Task on your Edge Device.

## Introduction

An MJPEG server running on your edge device, handling input and output, enabling model switching and parameter configuration.

## Features

- Auto-handling different input sources, such as MP4, IP cameras, and USB cameras.
- Dynamically switching AI models, currently supporting YOLOv8, but easily expandable.
- Simple and user-friendly MJPEG streaming output, accessible with just a browser, even on your phone.
- Publishes recognition results through MQTT, easily adaptable to your requirements.

## Usage Example

**Remind:** `Jetson orin nano 4G` can barely run, please try not to run other programs at the same time.

The easiest way is to run it using Docker. If you prefer running the source code directly on your local machine, please refer to the [Advanced Usage](#advanced-usage).

```sh
# maker sure Docker installed, and run the Edge in container
bash scripts/run.sh

# Demo: input[sample.mp4] with model[80-object-detect.engine]
# the initial startup may take some time.
# in machine 
http://localhost:46654/stream?src=sample.mp4&model_id=80-object-detect
# in other machine
http://machine-ip:46654/stream?src=sample.mp4&model_id=80-object-detect
```

## Advanced Usage

- if you want run with python in host, check [Run In Host](docs/run-in-host.md)
- more details about Docker, check [Run with Docker](docs/run-with-docker.md)
- the output-stream is MJPEG-stream, check [MJPEG](docs/mjpeg.md)
- the UI for the Edge from Seeed Studio, check [Web UI](docs/web-ui.md)
- the output of inference working with MQTT, check [MQTT Output](docs/mqtt-output.md)
- add your models, check [Design #models](docs/design.md#models)
- add your source or upload source, check [Design #input](docs/design.md#input)

## License

This project is released under the [MIT license](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for more information.

## History

See [CHANGELOG.md](CHANGELOG.md).
