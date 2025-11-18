class MonitorController {
  constructor() {
    this.streams = [];
    this.streamElements = new Map();
    this.focusStreamId = null;
    this.isStreaming = false;
    this.statsInterval = null;
    this.mqttInterval = null;

    this.initializeElements();
    this.initializeEventListeners();
    this.startStatsMonitoring();
    this.autoStartMonitoring();
  }

  initializeElements() {
    this.videoGrid = document.getElementById('videoGrid');
    this.currentTimeElement = document.getElementById('currentTime');
    this.lineCrossingPanel = document.getElementById('lineCrossingPanel');
    this.enterCountElement = document.getElementById('enterCount');
    this.exitCountElement = document.getElementById('exitCount');
  }

  initializeEventListeners() {
    // 当前版本保留接口，方便未来扩展按钮事件
  }

  async autoStartMonitoring() {
    try {
      let config = null;
      try {
        const response = await industrialMonitor.request('/appConfigs');
        config = response || {};
      } catch (error) {
        console.warn('从服务器获取配置失败，使用本地配置:', error);
        config = industrialMonitor.storage.get('appConfig', {});
      }

      this.initializeStreams(config);
    } catch (error) {
      console.error('自动启动监控失败:', error);
      this.showEmptyState('无法加载配置，请检查服务器');
      industrialMonitor.showNotification('自动启动失败: ' + error.message, 'error');
    }
  }

  initializeStreams(config = {}) {
    this.stopMqttMonitoring();
    const normalized = industrialMonitor.normalizeStreams(config.streams, config);
    const enabledStreams = normalized.filter((stream) => stream.enabled !== false);

    if (enabledStreams.length === 0) {
      this.showEmptyState('没有启用的监控流，请先在配置页添加并启用流');
      this.isStreaming = false;
      return;
    }

    this.streams = enabledStreams;
    const hasActive = enabledStreams.some((stream) => stream.id === config.active_stream_id);
    this.focusStreamId = hasActive ? config.active_stream_id : enabledStreams[0].id;

    this.streamElements.clear();
    this.videoGrid.innerHTML = '';

    enabledStreams.forEach((stream) => {
      const elements = this.createStreamCard(stream);
      this.streamElements.set(stream.id, elements);
      this.startStream(stream);
    });

    this.isStreaming = true;
    this.startMqttMonitoring();
  }

  createStreamCard(stream) {
    const card = document.createElement('div');
    card.className = 'video-card';

    const header = document.createElement('div');
    header.className = 'video-card-header';

    const titleWrap = document.createElement('div');
    titleWrap.className = 'video-card-title';
    titleWrap.textContent = stream.name || '未命名流';

    const subtitle = document.createElement('div');
    subtitle.className = 'video-card-subtitle';
    subtitle.textContent = stream.src || '未配置视频源';

    const status = document.createElement('span');
    status.className = 'stream-status status-waiting';
    status.textContent = '等待连接';

    const actionBtn = document.createElement('button');
    actionBtn.className = 'btn btn-secondary btn-sm';
    actionBtn.type = 'button';
    actionBtn.textContent = '⚙️ 配置';
    actionBtn.addEventListener('click', () => this.goToConfig());

    const headerActions = document.createElement('div');
    headerActions.className = 'video-card-actions';
    headerActions.appendChild(status);
    headerActions.appendChild(actionBtn);

    header.appendChild(titleWrap);
    header.appendChild(subtitle);
    header.appendChild(headerActions);

    const body = document.createElement('div');
    body.className = 'video-card-body';

    const img = document.createElement('img');
    img.className = 'video-stream';
    img.alt = stream.name || '视频流';
    // img.loading = 'lazy';

    const placeholder = document.createElement('div');
    placeholder.className = 'video-card-placeholder';
    placeholder.innerHTML = '<p>⏳ 正在准备连接...</p>';

    body.appendChild(img);
    body.appendChild(placeholder);

    const footer = document.createElement('div');
    footer.className = 'video-card-footer';

    const reconnectBtn = document.createElement('button');
    reconnectBtn.className = 'btn btn-primary btn-sm';
    reconnectBtn.type = 'button';
    reconnectBtn.textContent = '🔄 重连';
    reconnectBtn.addEventListener('click', () => this.reconnectStream(stream.id));

    footer.appendChild(reconnectBtn);

    card.appendChild(header);
    card.appendChild(body);
    card.appendChild(footer);

    this.videoGrid.appendChild(card);

    return { card, header, status, img, placeholder, reconnectBtn };
  }

  startStream(stream) {
    const elements = this.streamElements.get(stream.id);
    if (!elements) {
      return;
    }

    this.updateCardStatus(stream.id, '连接中', 'info');
    elements.placeholder.innerHTML = '<p>⏳ 正在连接...</p>';
    elements.placeholder.style.display = 'flex';
    elements.img.style.display = 'none';

    const streamUrl = industrialMonitor.buildStreamUrl({
      stream_id: stream.id,
      src: stream.src,
      model_id: stream.model_id,
      conf: stream.conf,
      max_det: stream.max_det,
      show_box: stream.show_box,
      track: stream.track,
      show_trail: stream.show_trail,
      trail_length: stream.trail_length,
      trail_thickness: stream.trail_thickness,
      trail_color: stream.trail_color,
      box_color: stream.box_color,
      half: stream.half,
      show_fps: stream.show_fps,
      show_time: stream.show_time,
      uuid: stream.uuid || stream.id,
    });

    elements.img.onload = () => this.handleStreamLoaded(stream.id);
    elements.img.onerror = () => this.handleStreamError(stream.id);
    elements.img.src = `${streamUrl}&ts=${Date.now()}`;
  }

  handleStreamLoaded(streamId) {
    const elements = this.streamElements.get(streamId);
    if (!elements) {
      return;
    }
    elements.placeholder.style.display = 'none';
    elements.img.style.display = 'block';
    this.updateCardStatus(streamId, '运行中', 'success');
  }

  handleStreamError(streamId) {
    const elements = this.streamElements.get(streamId);
    if (!elements) {
      return;
    }

    elements.img.style.display = 'none';
    elements.placeholder.style.display = 'flex';
    elements.placeholder.innerHTML = `
      <div class="video-error">
        <p>❌ 连接失败</p>
        <div class="video-error-actions">
          <button class="btn btn-warning btn-sm" onclick="monitorController.reconnectStream('${streamId}')">重新连接</button>
          <button class="btn btn-secondary btn-sm" onclick="monitorController.goToConfig()">检查配置</button>
        </div>
      </div>
    `;
    this.updateCardStatus(streamId, '连接失败', 'error');
  }

  updateCardStatus(streamId, text, state) {
    const elements = this.streamElements.get(streamId);
    if (!elements) {
      return;
    }
    elements.status.textContent = text;
    elements.status.className = `stream-status status-${state}`;
  }

  reconnectStream(streamId) {
    const stream = this.streams.find((item) => item.id === streamId);
    if (!stream) {
      industrialMonitor.showNotification('未找到对应的流配置', 'warning');
      return;
    }
    this.startStream(stream);
  }

  showEmptyState(message) {
    if (!this.videoGrid) {
      return;
    }
    this.videoGrid.innerHTML = `
      <div class="video-card placeholder-card">
        <div class="video-card-placeholder">
          <p>${message}</p>
          <button class="btn btn-primary btn-sm" onclick="monitorController.goToConfig()">前往配置</button>
        </div>
      </div>
    `;
  }

  goToConfig() {
    window.location.href = 'config.html';
  }

  startStatsMonitoring() {
    this.updateCurrentTime();
    this.statsInterval = setInterval(() => this.updateCurrentTime(), 1000);
  }

  updateCurrentTime() {
    const now = new Date();
    const timeString = now.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
    this.currentTimeElement.textContent = timeString;
  }

  startMqttMonitoring() {
    if (this.mqttInterval) {
      clearInterval(this.mqttInterval);
    }
    this.loadMqttData();
    this.mqttInterval = setInterval(() => this.loadMqttData(), 2000);
  }

  stopMqttMonitoring() {
    if (this.mqttInterval) {
      clearInterval(this.mqttInterval);
      this.mqttInterval = null;
    }
  }

  async loadMqttData() {
    try {
      const response = await industrialMonitor.request('/mqtt/data');
      this.updateDetectionDisplay(response.data || response);
    } catch (error) {
      console.error('加载MQTT数据失败:', error);
    }
  }

  updateDetectionDisplay(mqttData) {
    this.updateLineCrossingDisplay(mqttData);
  }

  updateLineCrossingDisplay(mqttData) {
    if (mqttData.line_crossing) {
      const enterCount = mqttData.line_crossing.enter || 0;
      const exitCount = mqttData.line_crossing.exit || 0;
      this.enterCountElement.textContent = enterCount;
      this.exitCountElement.textContent = exitCount;
      this.lineCrossingPanel.style.display = 'block';
    } else {
      this.lineCrossingPanel.style.display = 'none';
    }
  }
}

let monitorController;
document.addEventListener('DOMContentLoaded', () => {
  monitorController = new MonitorController();
});
