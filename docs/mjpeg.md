# mjpeg-stream

MJPEG (Motion JPEG) is a video compression format that represents moving images as a sequence of JPEG (Joint Photographic Experts Group) images.

## access with web browser

- localhost: access mjpeg url like this `http://127.0.0.1:46654/stream`
- LAN: access mjpeg url like this `http://192.168.x.x:46654/stream`
- some params(all optional), more details check the [urlparams_load()](src/streamer.py):
  - `src`: input source, which can be local video, rtsp address, and local camera path
  - `model_id`: The ID of the model is currently from the cloud OSS
  - `quality`: output video quality, 0-100
  - `fps`: The target fps of the output stream is the upper limit of the input source, which is affected by the recognition speed and input fps
  - `show_time`: when `show_time=1` display timestamp or `show_time=0` hide timestamp
  - `show_fps`:  when `show_fps=1` display fps or `show_fps=0` hide fps
  - `conf`: recognition threshold will only be checked if it is greater than this value
  - `max_det`: The maximum number of recognitions within a single frame
  - `uuid`: If mqtt is enabled, it is used to specify the recognition result of the current output stream

```sh
# Give a few examples, change these params for your requirements

# USB CAMERA, quality=95 fps=30 show-fps
http://127.0.0.1:46654/stream?src=/dev/video0&quality=95&fps=30&show_fps=1

# RTSP, uuid=rtsp
http://127.0.0.1:46654/stream?src=rtsp://admin:admin@x.x.x.x:y/z/stream1&uuid=rtsp

# MP4, show-time, conf>0.5, max-detect<=2
http://127.0.0.1:46654/stream?src=sample.mp4&show_time=1&conf=0.5&max_det=2
```

## download as mp4

```sh
# install tools
sudo apt install -y wget ffmpeg
# download mjpeg stream, use Ctrl+C stop the stream when you think it is enough
wget http://localhost:46654/stream -O output.mjpeg
# conver mjpeg to mp4
ffmpeg -f mjpeg -i output.mjpeg output.mp4ss
# play output.mp4 with the way you like
```
