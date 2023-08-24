# Design

Basic Idea: `cv2.VideoCapture() -[frame]-> yolov8.predict() -[mjpeg-strem]-> browser<img>`

## Input

- opencv get frame from source

### local source

- save your source in `sources/`

### remote source

- use `http://localhost:46654/sources/upload` or `http://machine-ip:46654/sources/upload` to access the simple html for upload your source

## Output

### mjpeg-stream

- frame after inference convert to mjpeg stream
- access output-stream like `http://localhost:46654/stream?src=sample.mp4&show_time=1&conf=0.5&max_det=2`

### inference-result

- inference result will be published to MQTT-broker
- subscribe like `mosquitto_sub -t edgeai/result`, and get the message like this:

```log
{"uuid": "8b749619-ad1b-493c-966a-c05af0bd87ef", "info": {"person": 8, "traffic light": 2, "backpack": 1, "handbag": 2}}
```

## Models

### local model

- 1 save your model file in `models/`, make its name simple because it will be used as url params
- 2 in `src/constant.py`, modify `DEFAULT_MODEL_LIST` add Item for new models, [jump to code](../src/constant.py#L8)

```python
#  Item Format
{
    "downloadUrl": "https://your-oss/models/80-object-detect.engine", # your model url, no matter if your model already in models/
    "name": "Object Dectect(TensorRT,SMALL,COCO)", # your model name
    "size": 24727, # model size, just save information for this model
    "icon": "https://your-oss/models/icon/detect.png", # your model icon url
    "arguments": {
        "uuid": "80-object-detect", # important! Model's name
        "type": "TensorRT", # important! Model's Type
        "task": "detect", # Optional, default=detect
        "half": True, # Optional, just save information for this model
    }
}
# local mode, need restart Edge to reload Model List
# using this model with url, like http://localhost:46654/stream?model_id=80-object-detect
```

### remote model

- upload [oss/models.json](../oss/models.json) to your oss
- in `src/constant.py`, modify [CLOUD_MODEL_CONFIG_URL](../src/constant.py#L27) to your oss-url for `models.json`
- after that, all you need to do is make sure all url can access in online's `models.json`
- and use `fileMgr.sync_cloud_model_list()` to sync cloud model list, without restart Edge.
