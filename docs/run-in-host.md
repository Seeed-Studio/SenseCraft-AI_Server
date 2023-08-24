# Run In Host

- this way to run allow you to modify the source code directly.

## File Structure

- `src/` python codes directory
  - `main.py` run everything
- `scripts/` shell scripts for simplify operations
  - `build.sh` build the Docker Image
  - `run.sh` run in Docker Containers

## Installation

```sh
# TODO: so many things installed complex env for different device
xxxx

# install mqtt-broker for receive the results of prediction
sudo apt update
sudo apt install mosquitto

# install python dependencies
pip install -r requirements.txt

# if mqtt-broker not installed
EDGEAI_MQTT_STARTUP=OFF python3 src/main.py

# offline mode run(using model and source in repo)
python3 src/main.py

# online mode (will download about 350MB models at first run)
EDGEAI_ONLINE=ON python3 src/main.py
```
