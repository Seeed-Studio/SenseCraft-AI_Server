CMD_TOPIC = "edgeai/cmd"
RESULT_TOPIC = "edgeai/result"
MODEL_FORMAT_MAP = {
    "yolov8": ".pt",
    "PyTorch": ".pt",
    "TensorRT": ".engine",
    "ONNX": ".onnx",
}

# 默认模型列表 - 仅作为备用
DEFAULT_MODEL_LIST = {
    "versionCode": 0,
    "versionName": "0.0.0",
    "updatedAt": 0,
    "modeList": [
        {
            "downloadUrl": "",
            "name": "80-object-detect (TensorRT)",
            "size": 0,
            "icon": "",
            "arguments": {
                "uuid": "80-object-detect",
                "type": "TensorRT",
                "task": "detect",
                "half": True,
            },
        },
    ],
}

SOURCE_UPLOAD_HTML = """
        <!doctype html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>上传源文件</title>
        </head>
        <body>
            <h1>上传源文件</h1>
            <form action="/upload" method="POST" enctype="multipart/form-data">
                <input type="file" name="file"><br><br>
                <input type="submit" value="上传">
            </form>
        </body>
        </html>
        """
