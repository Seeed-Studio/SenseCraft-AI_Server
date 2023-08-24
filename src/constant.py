CMD_TOPIC = "edgeai/cmd"
RESULT_TOPIC = "edgeai/result"
MODEL_FORMAT_MAP = {
    "yolov8": ".pt",
    "PyTorch": ".pt",
    "TensorRT": ".engine",
}
DEFAULT_MODEL_LIST = {
    "versionCode": 0,
    "versionName": "0.0.0",
    "updatedAt": 0,
    "modeList": [
        {
            "downloadUrl": "https://your-oss/models/80-object-detect.engine",
            "name": "Object Dectect(TensorRT,SMALL,COCO)",
            "size": 24727,
            "icon": "https://your-oss/models/icon/detect.png",
            "arguments": {
                "uuid": "80-object-detect",
                "type": "TensorRT",
                "task": "detect",
                "half": True,
            },
        },
    ],
}
CLOUD_MODEL_CONFIG_URL = "https://your-oss/models/models.json"
CLOUD_SAMPLE_VIDEO_URL = "https://your-oss/source/sample.mp4"

SOURCE_UPLOAD_HTML = """
        <!doctype html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>upload test</title>
        </head>
        <body>
            <h1>upload test</h1>
            <form action="/upload" method="POST" enctype="multipart/form-data">
                <input type="file" name="file"><br><br>
                <input type="submit" value="upload">
            </form>
        </body>
        </html>
        """
