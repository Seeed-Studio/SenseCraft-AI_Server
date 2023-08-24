# Run With Docker

Using Docker to run is a good way to ignore plenty of dependencies.

Before start everything, make sure your machine installed Docker.

```sh
# check the output
sudo docker --version
# such as `Docker version 20.10.21, build 20.10.21-0ubuntu1~20.04.2` is OK to go
```

## Seeed Image (recommend)

Building a custom image is quite complex, some solutions may be provided in the future. So the recommended method is directly use the image we have already created and pushed.

more details check [seeedcloud/edge-gateway](https://hub.docker.com/r/seeedcloud/edge-gateway/tags)

```sh
# can ignore this line, docker will auto-pull before run
docker pull seeedcloud/edge-gateway:mis-1.0
# if you had mqtt-broker, make sure `-e EDGEAI_MQTT_STARTUP="ON"`, default mqtt is OFF
bash scripts/run.sh
```

## Custom Image

- just for reference, not recommend!
- when you read this part, make sure you know what are you doing.

### Dockerfile

```Dockerfile
# https://catalog.ngc.nvidia.com/orgs/nvidia/containers/l4t-pytorch
FROM nvcr.io/nvidia/l4t-pytorch:r35.2.1-pth2.0-py3
# Numba makes Python code fast
RUN pip install numba
# YOLOv8
RUN pip install ultralytics
# FIX:  AttributeError: partially initialized module 'cv2' has no attribute '_registerMatType' (most likely due to a circular import)
RUN pip install "opencv-python-headless<4.3"
# work zone
WORKDIR /opt/dev/
# project modules 1 requirement.txt
COPY requirements.txt /opt/dev/
# project modules 2 install
RUN pip install -r /opt/dev/requirements.txt
# FIX: support TensorRT , must after `pip install ultralytics`
RUN pip install numpy==1.23.5
# copy base models
COPY models/ /opt/dev/models/
# copy base configs
COPY configs/ /opt/dev/configs/
# copy source sample.mp4
COPY sources/ /opt/dev/sources/
# copy src
COPY src/ /opt/dev/src/
# RUN main.py
CMD [ "python3", "/opt/dev/src/main.py", "2>&1" ]
```

### Build Image

```sh
sudo docker build ./ -t yolo-mjpeg:v0.0.1
```

### Run Container

```sh
# remove old
sudo docker rm -f edge-ai-backend
# run new
sudo docker run -d \
--runtime=nvidia \
--restart=always \
--network=host \
--privileged \
--name=edge-ai-backend \
-e EDGEAI_LOG_LEVEL="20" \
-e EDGEAI_MQTT_STARTUP="ON" \
-e EDGEAI_MODELS_PATH="/opt/dev/models/" \
-e EDGEAI_SOURCES_PATH="/opt/dev/sources/" \
-e EDGEAI_CONFIGS_PATH="/opt/dev/configs/" \
-e EDGEAI_WEB_DIST_PATH="/opt/dev/dist/" \
-e EDGEAI_PORT="46654" \
-v $PWD/models:/opt/dev/models/ \
-v $PWD/configs:/opt/dev/configs/ \
-v $PWD/sources:/opt/dev/sources/ \
-v $PWD/dist:/opt/dev/dist/ \
-v /usr/bin/tegrastats:/usr/bin/tegrastats \
-v /sys:/sys -v /proc:/proc \
-v /dev:/dev \
yolo-mjpeg:v0.0.1
# follow log
sudo docker logs edge-ai-backend -f
```
