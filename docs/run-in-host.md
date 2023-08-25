# Run In Host

The following information will help you understand the code structure and support you in modifying the source code according to your own ideas for execution

## File Structure

- `src/` python codes directory
  - `main.py` init logger, and start everything
  - `camera.py` read input frame by frame, infer, and write output
  - `output.py` save output for streaming
  - `streamer.py` create mjpeg-stream and provide http-API
  - `file_manager.py` manage sources, models, and configurations
  - `mqtt_handler.py` connect to mqtt
- `scripts/` shell scripts for simplify operations
  - `run.sh` run in Docker Containers
- `configs/` save application configurations
  - `application.json` save stream configs for webUI
- `models/` save AI-Models
  - `80-object-detect.engine` a sample model, tensorrt model
- `sources/` save sources
  - `sample.mp4` a sample video
- `oss/` save files need to upload to OSS
  - `models.json` a sample cloud model list
- `docs/` documents for this project

## Installation

**ATTENTION!!**

- Different machines have different environmental requirements.
- Please ensure that you have the capability to research and resolve complex prerequisites.
- Otherwise, we recommend using Docker for running the application, follow [Run With Docker](run-with-docker.md#seeed-image-recommend).

```sh
# if your model is pytorch format, such as *.pt, you need install pytorch
echo "Depending on your machine, find the correct method to install PyTorch."
# Numba makes some python code faster
pip install numba
# YOLOv8
pip install ultralytics
# FIX: AttributeError: partially initialized module 'cv2' has no attribute '_registerMatType' (most likely due to a circular import)
pip install "opencv-python-headless<4.3"
# FIX: support TensorRT, must after `pip install ultralytics`
pip install numpy==1.23.5

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
