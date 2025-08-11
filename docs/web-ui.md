# Web Interface

SenseCraft AI Server provides a comprehensive web interface for easy configuration and monitoring.

## Quick Start

After starting the server, simply access:

```sh
# Local access
http://localhost:46654/

# Remote access (replace with your machine's IP)
http://your-machine-ip:46654/
```

## Features

### 🎮 Main Control Panel
- **Video Source Configuration**: Select from local files, USB cameras, or RTSP streams
- **AI Model Selection**: Choose from available models with real-time switching
- **Parameter Tuning**: Adjust confidence, detection limits, and display options
- **Stream Control**: Start, stop, pause, and resume video streams

### 📁 File Management
- **Upload Videos**: Drag and drop video files for processing
- **Upload Models**: Add new AI models in various formats
- **File Management**: View, delete, and organize uploaded files
- **Collapsible Interface**: Clean, organized layout with expandable sections

### 📊 Real-time Monitoring
- **Live Video Stream**: MJPEG streaming with AI overlay
- **MQTT Integration**: Real-time detection results via MQTT
- **Status Indicators**: Connection status, FPS, and detection counts
- **Performance Metrics**: Monitor system performance in real-time

### ⚙️ Advanced Features
- **Model Hot-swapping**: Change models without restarting
- **Parameter Persistence**: Settings are saved and restored
- **Responsive Design**: Works on desktop and mobile devices
- **Error Handling**: Clear feedback for configuration issues

## Usage

1. **Start the Server**: Run `bash scripts/run.sh`
2. **Open Browser**: Navigate to `http://localhost:46654/`
3. **Configure Settings**: Select video source and AI model
4. **Start Streaming**: Click "开始推理" to begin
5. **Monitor Results**: View live stream and MQTT data

## Technical Details

The web interface is built with:
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Backend**: Python HTTP server with MJPEG streaming
- **Communication**: RESTful APIs for configuration
- **Real-time**: WebSocket-like streaming for video

For advanced configuration and API details, see:
- [File Upload Features](UPLOAD_FEATURES.md)
- [MQTT Output](mqtt-output.md)
- [System Design](design.md)
