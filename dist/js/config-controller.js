class ConfigController {
  constructor() {
    this.sources = [];
    this.models = [];
    this.streams = [];
    this.activeStreamId = null;
    this.streamsInitialized = false;

    this.initializeElements();
    this.initializeEventListeners();
    this.startTimeUpdate();
    this.loadData();
  }

  initializeElements() {
    this.videoSource = document.getElementById('videoSource');
    this.rtspInputGroup = document.getElementById('rtspInputGroup');
    this.rtspUrl = document.getElementById('rtspUrl');
    this.modelSelect = document.getElementById('modelSelect');
    this.confidence = document.getElementById('confidence');
    this.maxDetections = document.getElementById('maxDetections');
    this.halfPrecision = document.getElementById('halfPrecision');
    this.showFps = document.getElementById('showFps');
    this.showTime = document.getElementById('showTime');
    this.showBox = document.getElementById('showBox');
    this.boxColor = document.getElementById('boxColor');
    this.tracking = document.getElementById('tracking');
    this.showTrail = document.getElementById('showTrail');
    this.trailConfig = document.getElementById('trailConfig');
    this.trailLength = document.getElementById('trailLength');
    this.trailThickness = document.getElementById('trailThickness');
    this.trailColor = document.getElementById('trailColor');

    this.streamTabs = document.getElementById('streamTabs');
    this.addStreamBtn = document.getElementById('addStreamBtn');
    this.streamNameInput = document.getElementById('streamName');
    this.streamEnabledInput = document.getElementById('streamEnabled');

    this.lineCrossingEnabled = document.getElementById('lineCrossingEnabled');
    this.lineCrossingConfig = document.getElementById('lineCrossingConfig');
    this.lineDirection = document.getElementById('lineDirection');
    this.lineX1 = document.getElementById('lineX1');
    this.lineY1 = document.getElementById('lineY1');
    this.lineX2 = document.getElementById('lineX2');
    this.lineY2 = document.getElementById('lineY2');
    this.lineTolerance = document.getElementById('lineTolerance');
    this.lineColor = document.getElementById('lineColor');
    this.lineThickness = document.getElementById('lineThickness');
    this.showLine = document.getElementById('showLine');
    this.showCounts = document.getElementById('showCounts');

    this.currentTimeElement = document.getElementById('currentTime');
    this.streamCountElement = document.getElementById('streamCount');
    this.configStatusElement = document.getElementById('configStatus');
  }

  initializeEventListeners() {
    this.videoSource.addEventListener('change', (e) => {
      this.toggleRtspInput(e.target.value);
      this.updateStreamSource();
    });

    this.rtspUrl.addEventListener('input', () => {
      if (this.videoSource.value === 'rtsp://') {
        this.updateStreamField('src', this.rtspUrl.value);
      }
    });

    this.streamNameInput.addEventListener('input', (e) => {
      this.updateStreamField('name', e.target.value || '');
      this.renderStreamTabs();
    });

    this.streamEnabledInput.addEventListener('change', (e) => {
      this.updateStreamField('enabled', e.target.checked);
      this.renderStreamTabs();
    });

    this.modelSelect.addEventListener('change', () => {
      this.updateStreamField('model_id', this.modelSelect.value);
    });

    this.confidence.addEventListener('input', (e) => {
      document.getElementById('confValue').textContent = e.target.value;
      this.updateStreamField('conf', e.target.value);
    });

    this.maxDetections.addEventListener('input', (e) => {
      document.getElementById('maxDetValue').textContent = e.target.value;
      this.updateStreamField('max_det', e.target.value);
    });

    this.showTrail.addEventListener('change', (e) => {
      this.trailConfig.style.display = e.target.checked ? 'block' : 'none';
      this.updateStreamField('show_trail', e.target.checked ? '1' : '0');
    });

    this.trailLength.addEventListener('input', (e) => {
      document.getElementById('trailLengthValue').textContent = e.target.value;
      this.updateStreamField('trail_length', e.target.value);
    });

    this.trailThickness.addEventListener('input', (e) => {
      document.getElementById('trailThicknessValue').textContent = e.target.value;
      this.updateStreamField('trail_thickness', e.target.value);
    });

    const booleanBindings = [
      { element: this.halfPrecision, field: 'half' },
      { element: this.showFps, field: 'show_fps' },
      { element: this.showTime, field: 'show_time' },
      { element: this.showBox, field: 'show_box' },
      { element: this.tracking, field: 'track' },
    ];

    booleanBindings.forEach(({ element, field }) => {
      element.addEventListener('change', (event) => {
        this.updateStreamField(field, event.target.checked ? '1' : '0');
      });
    });

    this.boxColor.addEventListener('change', (e) => {
      this.updateStreamField('box_color', e.target.value);
    });

    this.trailColor.addEventListener('change', (e) => {
      this.updateStreamField('trail_color', e.target.value);
    });

    this.lineCrossingEnabled.addEventListener('change', (e) => {
      this.lineCrossingConfig.style.display = e.target.checked ? 'block' : 'none';
      this.updateConfigPreview();
    });

    this.lineDirection.addEventListener('change', () => {
      this.updateLineCoordinates();
      this.updateConfigPreview();
    });

    [
      { element: this.lineX1, label: 'lineX1Value' },
      { element: this.lineY1, label: 'lineY1Value' },
      { element: this.lineX2, label: 'lineX2Value' },
      { element: this.lineY2, label: 'lineY2Value' },
      { element: this.lineTolerance, label: 'lineToleranceValue' },
      { element: this.lineThickness, label: 'lineThicknessValue' },
    ].forEach(({ element, label }) => {
      element.addEventListener('input', (e) => {
        document.getElementById(label).textContent = e.target.value;
        this.updateConfigPreview();
      });
    });

    this.showLine.addEventListener('change', () => this.updateConfigPreview());
    this.showCounts.addEventListener('change', () => this.updateConfigPreview());

    document.getElementById('uploadVideoBtn').addEventListener('click', () => this.uploadVideo());
    document.getElementById('uploadModelBtn').addEventListener('click', () => this.uploadModel());

    document.getElementById('saveConfigBtn').addEventListener('click', () => this.saveConfig());
    document.getElementById('loadConfigBtn').addEventListener('click', () => this.loadConfig());
    document.getElementById('resetConfigBtn').addEventListener('click', () => this.resetConfig());
    document.getElementById('exportConfigBtn').addEventListener('click', () => this.exportConfig());
    document.getElementById('importConfigBtn').addEventListener('click', () => this.importConfig());

    document.getElementById('resetLineCountsBtn').addEventListener('click', () => this.resetLineCounts());
    document.getElementById('startMonitorBtn').addEventListener('click', () => this.startMonitor());
    this.addStreamBtn.addEventListener('click', () => this.addStream());
  }

  async loadData() {
    await Promise.all([this.loadSources(), this.loadModels()]);
    setTimeout(() => {
      this.loadSavedConfig();
    }, 100);
  }

  async loadSources() {
    try {
      const response = await industrialMonitor.request('/sources/list');
      this.sources = response.list || [];
      this.populateSourceSelect();
      this.updateSourceList();
      this.updateSourceCount();
      if (this.streamsInitialized) {
        this.applyStreamToForm(this.getActiveStream());
      }
    } catch (error) {
      console.error('加载视频源失败:', error);
      industrialMonitor.showError('sourceError', '加载视频源失败: ' + error.message);
    }
  }

  async loadModels() {
    try {
      const response = await industrialMonitor.request('/models/list');
      this.models = response.list || [];
      this.populateModelSelect();
      this.updateModelList();
      this.updateModelCount();
      if (this.streamsInitialized) {
        this.applyStreamToForm(this.getActiveStream());
      }
    } catch (error) {
      console.error('加载模型失败:', error);
      industrialMonitor.showError('modelError', '加载模型失败: ' + error.message);
    }
  }

  populateSourceSelect() {
    this.videoSource.innerHTML = '';
    this.sources.forEach((source) => {
      const option = document.createElement('option');
      option.value = source;
      option.textContent = `本地视频 (${source})`;
      this.videoSource.appendChild(option);
    });

    const cameraOption = document.createElement('option');
    cameraOption.value = '/dev/video0';
    cameraOption.textContent = 'USB摄像头 (/dev/video0)';
    this.videoSource.appendChild(cameraOption);

    const rtspOption = document.createElement('option');
    rtspOption.value = 'rtsp://';
    rtspOption.textContent = 'RTSP流';
    this.videoSource.appendChild(rtspOption);
  }

  populateModelSelect() {
    this.modelSelect.innerHTML = '';
    this.models.forEach((model) => {
      const option = document.createElement('option');
      const modelId = model.arguments?.uuid || model.uuid || model.id || model.filename || model.name;
      option.value = modelId;
      option.textContent = model.name || model.filename || modelId;
      this.modelSelect.appendChild(option);
    });
  }

  updateSourceList() {
    const sourceList = document.getElementById('sourceList');
    if (this.sources.length === 0) {
      sourceList.innerHTML = '<div class="text-center" style="color: var(--text-muted); padding: 20px;">暂无视频源</div>';
      return;
    }

    sourceList.innerHTML = '';
    this.sources.forEach((source) => {
      const item = document.createElement('div');
      item.className = 'source-item';
      item.innerHTML = `
        <div>
          <div class="source-name">${source}</div>
          <div class="file-info">本地视频文件</div>
        </div>
        <div class="source-actions">
          <button class="btn btn-sm btn-delete" onclick="configController.deleteSource('${source}')">删除</button>
        </div>
      `;
      sourceList.appendChild(item);
    });
  }

  updateModelList() {
    const modelList = document.getElementById('modelList');
    if (this.models.length === 0) {
      modelList.innerHTML = '<div class="text-center" style="color: var(--text-muted); padding: 20px;">暂无模型</div>';
      return;
    }

    modelList.innerHTML = '';
    this.models.forEach((model) => {
      const item = document.createElement('div');
      item.className = 'model-item';
      const modelId = model.arguments?.uuid || model.uuid || model.id || model.filename || model.name;
      const modelName = model.name || model.filename || modelId;
      const deleteTarget = model.filename || model.name || modelId;
      item.innerHTML = `
        <div>
          <div class="model-name">${modelName}</div>
          <div class="file-info">${modelId}</div>
        </div>
        <div class="model-actions">
          <button class="btn btn-sm btn-delete" onclick="configController.deleteModel('${deleteTarget}')">删除</button>
        </div>
      `;
      modelList.appendChild(item);
    });
  }

  updateSourceCount() {
    document.getElementById('sourceCount').textContent = this.sources.length;
  }

  updateModelCount() {
    document.getElementById('modelCount').textContent = this.models.length;
  }

  updateStreamCount() {
    if (this.streamCountElement) {
      this.streamCountElement.textContent = this.streams.length;
    }
  }

  toggleRtspInput(sourceType) {
    this.rtspInputGroup.style.display = sourceType === 'rtsp://' ? 'block' : 'none';
  }

  updateStreamSource() {
    const selected = this.videoSource.value;
    if (selected === 'rtsp://') {
      this.updateStreamField('src', this.rtspUrl.value || '');
    } else {
      this.updateStreamField('src', selected);
    }
  }

  normalizeStreams(config = {}) {
    const fallback = {
      src: config.src,
      model_id: config.model_id,
      conf: config.conf,
      max_det: config.max_det,
      half: config.half,
      show_fps: config.show_fps,
      show_time: config.show_time,
      show_box: config.show_box,
      box_color: config.box_color,
      track: config.track,
      show_trail: config.show_trail,
      trail_length: config.trail_length,
      trail_thickness: config.trail_thickness,
      trail_color: config.trail_color,
      uuid: config.uuid,
    };
    return industrialMonitor.normalizeStreams(config.streams, fallback).map((stream, index) => ({
      ...stream,
      name: stream.name || `流${index + 1}`,
    }));
  }

  renderStreamTabs() {
    if (!this.streamTabs) {
      return;
    }

    this.streamTabs.innerHTML = '';
    if (this.streams.length === 0) {
      this.streamTabs.innerHTML = '<div class="text-center" style="color: var(--text-muted);">暂无监控流</div>';
      return;
    }

    this.streams.forEach((stream) => {
      const tab = document.createElement('button');
      tab.type = 'button';
      tab.className = `stream-tab${stream.id === this.activeStreamId ? ' active' : ''}${stream.enabled === false ? ' disabled' : ''}`;
      tab.textContent = stream.name || '未命名';
      tab.addEventListener('click', () => this.setActiveStream(stream.id));

      if (this.streams.length > 1) {
        const removeBtn = document.createElement('span');
        removeBtn.className = 'remove-tab';
        removeBtn.textContent = '×';
        removeBtn.addEventListener('click', (event) => {
          event.stopPropagation();
          this.removeStream(stream.id);
        });
        tab.appendChild(removeBtn);
      }

      if (stream.enabled === false) {
        const badge = document.createElement('span');
        badge.className = 'stream-tab-status';
        badge.textContent = '暂停';
        tab.appendChild(badge);
      }

      this.streamTabs.appendChild(tab);
    });
  }

  addStream() {
    this.syncStreamFromForm();
    const newStream = industrialMonitor.createStreamConfig({}, this.streams.length);
    newStream.name = `流${this.streams.length + 1}`;
    this.streams.push(newStream);
    this.updateStreamCount();
    this.setActiveStream(newStream.id);
    industrialMonitor.showNotification('已新增监控流', 'success');
  }

  removeStream(streamId) {
    if (this.streams.length <= 1) {
      industrialMonitor.showNotification('至少保留一个监控流', 'warning');
      return;
    }

    this.streams = this.streams.filter((stream) => stream.id !== streamId);
    if (this.activeStreamId === streamId) {
      this.activeStreamId = this.streams[0].id;
    }
    this.updateStreamCount();
    this.renderStreamTabs();
    this.applyStreamToForm(this.getActiveStream());
    this.updateConfigPreview();
  }

  setActiveStream(streamId) {
    this.syncStreamFromForm();
    this.activeStreamId = streamId;
    this.renderStreamTabs();
    this.applyStreamToForm(this.getActiveStream());
    this.updateConfigPreview();
  }

  getActiveStream() {
    if (this.streams.length === 0) {
      const stream = industrialMonitor.createStreamConfig({}, 0);
      this.streams.push(stream);
      this.activeStreamId = stream.id;
      this.updateStreamCount();
    }
    return this.streams.find((stream) => stream.id === this.activeStreamId) || this.streams[0];
  }

  updateStreamField(field, value) {
    const stream = this.getActiveStream();
    if (!stream) return;
    stream[field] = value;
    this.updateConfigPreview();
  }

  applyStreamToForm(stream) {
    if (!stream) {
      return;
    }

    const availableSources = Array.from(this.videoSource.options).map((option) => option.value);
    if (stream.src && availableSources.includes(stream.src)) {
      this.videoSource.value = stream.src;
      this.toggleRtspInput(stream.src);
      this.rtspUrl.value = '';
    } else if (stream.src && stream.src.startsWith('rtsp://')) {
      this.videoSource.value = 'rtsp://';
      this.rtspUrl.value = stream.src;
      this.toggleRtspInput('rtsp://');
    } else {
      this.videoSource.value = '';
      this.toggleRtspInput('');
      this.rtspUrl.value = stream.src || '';
    }

    if (stream.model_id) {
      const modelExists = Array.from(this.modelSelect.options).some((option) => option.value === stream.model_id);
      if (modelExists) {
        this.modelSelect.value = stream.model_id;
      }
    }

    this.streamNameInput.value = stream.name || '';
    this.streamEnabledInput.checked = stream.enabled !== false;

    this.confidence.value = stream.conf || '0.25';
    document.getElementById('confValue').textContent = this.confidence.value;

    this.maxDetections.value = stream.max_det || '300';
    document.getElementById('maxDetValue').textContent = this.maxDetections.value;

    this.halfPrecision.checked = this.isEnabled(stream.half);
    this.showFps.checked = this.isEnabled(stream.show_fps);
    this.showTime.checked = this.isEnabled(stream.show_time);
    this.showBox.checked = this.isEnabled(stream.show_box, true);
    this.tracking.checked = this.isEnabled(stream.track);

    this.boxColor.value = stream.box_color || 'orange';

    this.showTrail.checked = this.isEnabled(stream.show_trail);
    this.trailConfig.style.display = this.showTrail.checked ? 'block' : 'none';
    this.trailLength.value = stream.trail_length || '50';
    document.getElementById('trailLengthValue').textContent = this.trailLength.value;
    this.trailThickness.value = stream.trail_thickness || '2';
    document.getElementById('trailThicknessValue').textContent = this.trailThickness.value;
    this.trailColor.value = stream.trail_color || 'blue';

    this.updateConfigPreview();
  }

  syncStreamFromForm() {
    const stream = this.getActiveStream();
    if (!stream) {
      return;
    }

    stream.name = this.streamNameInput.value || stream.name;
    stream.enabled = this.streamEnabledInput.checked;
    stream.model_id = this.modelSelect.value;
    stream.conf = this.confidence.value;
    stream.max_det = this.maxDetections.value;
    stream.half = this.halfPrecision.checked ? '1' : '0';
    stream.show_fps = this.showFps.checked ? '1' : '0';
    stream.show_time = this.showTime.checked ? '1' : '0';
    stream.show_box = this.showBox.checked ? '1' : '0';
    stream.box_color = this.boxColor.value;
    stream.track = this.tracking.checked ? '1' : '0';
    stream.show_trail = this.showTrail.checked ? '1' : '0';
    stream.trail_length = this.trailLength.value;
    stream.trail_thickness = this.trailThickness.value;
    stream.trail_color = this.trailColor.value;
    stream.src = this.videoSource.value === 'rtsp://' ? (this.rtspUrl.value || '') : this.videoSource.value;
  }

  isEnabled(value, defaultValue = true) {
    if (value === undefined || value === null || value === '') {
      return defaultValue;
    }
    if (typeof value === 'boolean') {
      return value;
    }
    return value !== '0' && value !== 'false';
  }

  getCurrentConfig() {
    this.syncStreamFromForm();
    const stream = { ...this.getActiveStream() };
    stream.line_crossing = this.getLineCrossingConfig();
    return stream;
  }

  buildSavePayload() {
    const current = this.getCurrentConfig();
    return {
      ...current,
      streams: this.streams.map((stream) => ({ ...stream })),
      active_stream_id: this.activeStreamId,
      line_crossing: current.line_crossing,
    };
  }

  updateConfigPreview() {
    const config = this.getCurrentConfig();
    const stream = this.getActiveStream();
    const preview = document.getElementById('configPreview');

    preview.innerHTML = `
      <div class="info-item">
        <span class="info-label">流名称:</span>
        <span class="info-value">${stream?.name || '未命名'}</span>
      </div>
      <div class="info-item">
        <span class="info-label">流状态:</span>
        <span class="info-value">${stream?.enabled !== false ? '启用' : '暂停'}</span>
      </div>
      <div class="info-item">
        <span class="info-label">视频源:</span>
        <span class="info-value">${config.src || '未选择'}</span>
      </div>
      <div class="info-item">
        <span class="info-label">AI模型:</span>
        <span class="info-value">${config.model_id || '未选择'}</span>
      </div>
      <div class="info-item">
        <span class="info-label">置信度:</span>
        <span class="info-value">${config.conf}</span>
      </div>
      <div class="info-item">
        <span class="info-label">最大检测:</span>
        <span class="info-value">${config.max_det}</span>
      </div>
      <div class="info-item">
        <span class="info-label">显示设置:</span>
        <span class="info-value">${this.getDisplaySettings(config)}</span>
      </div>
      <div class="info-item">
        <span class="info-label">跟踪设置:</span>
        <span class="info-value">${this.getTrackingSettings(config)}</span>
      </div>
      <div class="info-item">
        <span class="info-label">绊线检测:</span>
        <span class="info-value">${this.getLineCrossingSettings(config)}</span>
      </div>
    `;
  }

  getDisplaySettings(config) {
    const settings = [];
    if (config.show_fps === '1') settings.push('FPS');
    if (config.show_time === '1') settings.push('时间戳');
    if (config.show_box === '1') settings.push('检测框');
    return settings.length > 0 ? settings.join(', ') : '无';
  }

  getTrackingSettings(config) {
    const settings = [];
    if (config.track === '1') settings.push('目标跟踪');
    if (config.show_trail === '1') settings.push('轨迹线');
    return settings.length > 0 ? settings.join(', ') : '无';
  }

  getLineCrossingSettings(config) {
    if (!config.line_crossing || !config.line_crossing.enabled) {
      return '未启用';
    }
    const direction = config.line_crossing.direction === 'horizontal' ? '水平线' : '垂直线';
    const showLine = config.line_crossing.show_line !== false ? '显示绊线' : '隐藏绊线';
    const showCounts = config.line_crossing.show_counts !== false ? '显示计数' : '隐藏计数';
    return `${direction} (${config.line_crossing.x1},${config.line_crossing.y1}) - (${config.line_crossing.x2},${config.line_crossing.y2}) | ${showLine}, ${showCounts}`;
  }

  getLineCrossingConfig() {
    if (!this.lineCrossingEnabled.checked) {
      return { enabled: false };
    }
    return {
      enabled: true,
      direction: this.lineDirection.value,
      x1: parseInt(this.lineX1.value, 10),
      y1: parseInt(this.lineY1.value, 10),
      x2: parseInt(this.lineX2.value, 10),
      y2: parseInt(this.lineY2.value, 10),
      tolerance: parseInt(this.lineTolerance.value, 10),
      color: this.lineColor.value,
      thickness: parseInt(this.lineThickness.value, 10),
      show_line: this.showLine.checked,
      show_counts: this.showCounts.checked,
    };
  }

  updateLineCoordinates() {
    if (this.lineDirection.value === 'horizontal') {
      this.lineY2.value = this.lineY1.value;
      document.getElementById('lineY2Value').textContent = this.lineY1.value;
    } else {
      this.lineX2.value = this.lineX1.value;
      document.getElementById('lineX2Value').textContent = this.lineX1.value;
    }
  }

  async resetLineCounts() {
    if (!confirm('确定要重置绊线计数吗？')) {
      return;
    }

    try {
      await industrialMonitor.request('/line/reset');
      industrialMonitor.showNotification('绊线计数已重置', 'success');
    } catch (error) {
      console.error('重置绊线计数失败:', error);
      industrialMonitor.showNotification('重置失败: ' + error.message, 'error');
    }
  }

  async uploadVideo() {
    const fileInput = document.getElementById('videoUpload');
    const files = fileInput.files;
    if (files.length === 0) {
      industrialMonitor.showNotification('请选择要上传的视频文件', 'error');
      return;
    }

    const uploadBtn = document.getElementById('uploadVideoBtn');
    uploadBtn.disabled = true;
    industrialMonitor.showNotification('正在上传视频文件...', 'info');

    try {
      for (let i = 0; i < files.length; i += 1) {
        await industrialMonitor.uploadFile(files[i], '/upload');
      }
      industrialMonitor.showNotification(`成功上传 ${files.length} 个视频文件`, 'success');
      fileInput.value = '';
      await this.loadSources();
    } catch (error) {
      console.error('视频上传失败:', error);
      industrialMonitor.showNotification('上传失败: ' + error.message, 'error');
    } finally {
      uploadBtn.disabled = false;
    }
  }

  async uploadModel() {
    const fileInput = document.getElementById('modelUpload');
    const files = fileInput.files;
    if (files.length === 0) {
      industrialMonitor.showNotification('请选择要上传的模型文件', 'error');
      return;
    }

    const uploadBtn = document.getElementById('uploadModelBtn');
    uploadBtn.disabled = true;
    industrialMonitor.showNotification('正在上传模型文件...', 'info');

    try {
      for (let i = 0; i < files.length; i += 1) {
        await industrialMonitor.uploadFile(files[i], '/upload');
      }
      industrialMonitor.showNotification(`成功上传 ${files.length} 个模型文件`, 'success');
      fileInput.value = '';
      await this.loadModels();
    } catch (error) {
      console.error('模型上传失败:', error);
      industrialMonitor.showNotification('上传失败: ' + error.message, 'error');
    } finally {
      uploadBtn.disabled = false;
    }
  }

  async deleteSource(name) {
    if (!confirm(`确定要删除视频源 "${name}" 吗？`)) {
      return;
    }
    try {
      await industrialMonitor.request(`/sources/del?name=${encodeURIComponent(name)}`);
      industrialMonitor.showNotification('删除成功', 'success');
      await this.loadSources();
    } catch (error) {
      console.error('删除视频源失败:', error);
      industrialMonitor.showNotification('删除失败: ' + error.message, 'error');
    }
  }

  async deleteModel(name) {
    if (!confirm(`确定要删除模型 "${name}" 吗？`)) {
      return;
    }
    try {
      await industrialMonitor.request(`/models/del?name=${encodeURIComponent(name)}`);
      industrialMonitor.showNotification('删除成功', 'success');
      await this.loadModels();
    } catch (error) {
      console.error('删除模型失败:', error);
      industrialMonitor.showNotification('删除失败: ' + error.message, 'error');
    }
  }

  async saveConfig() {
    const payload = this.buildSavePayload();
    try {
      this.configStatusElement.textContent = '保存中...';
      industrialMonitor.showNotification('正在保存配置到服务器...', 'info');
      await industrialMonitor.request('/appConfigs', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      if (payload.line_crossing && payload.line_crossing.enabled) {
        await industrialMonitor.request('/line/config', {
          method: 'POST',
          body: JSON.stringify(payload.line_crossing),
        });
      }

      industrialMonitor.storage.set('appConfig', payload);
      this.configStatusElement.textContent = '已保存到服务器';
      industrialMonitor.showNotification('配置已成功保存到服务器', 'success');
    } catch (error) {
      console.error('保存配置失败:', error);
      this.configStatusElement.textContent = '保存失败';
      industrialMonitor.showNotification('保存配置失败: ' + error.message, 'error');
    }
  }

  async loadConfig() {
    try {
      this.configStatusElement.textContent = '加载中...';
      industrialMonitor.showNotification('正在从服务器加载配置...', 'info');
      const response = await industrialMonitor.request('/appConfigs');
      const config = response || {};
      try {
        const lineConfig = await industrialMonitor.request('/line/config');
        if (lineConfig && lineConfig.enabled) {
          config.line_crossing = lineConfig;
        }
      } catch (err) {
        console.warn('加载绊线配置失败:', err);
      }
      this.applyConfig(config);
      this.configStatusElement.textContent = '已从服务器加载';
      industrialMonitor.showNotification('配置已从服务器加载', 'success');
    } catch (error) {
      console.error('从服务器加载配置失败:', error);
      industrialMonitor.showNotification('从服务器加载配置失败，尝试加载本地备份', 'warning');
      const localConfig = industrialMonitor.storage.get('appConfig', {});
      this.applyConfig(localConfig);
      this.configStatusElement.textContent = '已加载本地备份';
    }
  }

  resetConfig() {
    if (!confirm('确定要重置所有配置吗？')) {
      return;
    }
    this.applyDefaultConfig();
    this.configStatusElement.textContent = '已重置';
    industrialMonitor.showNotification('配置已重置', 'info');
  }

  exportConfig() {
    const payload = this.buildSavePayload();
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    industrialMonitor.downloadFile(url, 'sensecraft-config.json');
    URL.revokeObjectURL(url);
    industrialMonitor.showNotification('配置已导出', 'success');
  }

  importConfig() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = async (event) => {
      const file = event.target.files[0];
      if (!file) return;
      try {
        const text = await file.text();
        const config = JSON.parse(text);
        this.applyConfig(config);
        this.configStatusElement.textContent = '已导入';
        industrialMonitor.showNotification('配置已导入', 'success');
      } catch (error) {
        industrialMonitor.showNotification('导入失败: 文件格式错误', 'error');
      }
    };
    input.click();
  }

  applyConfig(config = {}) {
    this.streams = this.normalizeStreams(config);
    if (this.streams.length > 0) {
      const exists = this.streams.some((stream) => stream.id === config.active_stream_id);
      this.activeStreamId = exists ? config.active_stream_id : this.streams[0].id;
    }
    this.renderStreamTabs();
    this.applyStreamToForm(this.getActiveStream());
    this.streamsInitialized = true;
    this.updateStreamCount();
    this.applyLineConfig(config.line_crossing);
    this.updateConfigPreview();
  }

  applyLineConfig(lineConfig = null) {
    if (!lineConfig) {
      this.lineCrossingEnabled.checked = false;
      this.lineCrossingConfig.style.display = 'none';
      return;
    }

    this.lineCrossingEnabled.checked = lineConfig.enabled || false;
    this.lineCrossingConfig.style.display = lineConfig.enabled ? 'block' : 'none';

    if (lineConfig.direction) this.lineDirection.value = lineConfig.direction;
    if (lineConfig.x1 !== undefined) {
      this.lineX1.value = lineConfig.x1;
      document.getElementById('lineX1Value').textContent = lineConfig.x1;
    }
    if (lineConfig.y1 !== undefined) {
      this.lineY1.value = lineConfig.y1;
      document.getElementById('lineY1Value').textContent = lineConfig.y1;
    }
    if (lineConfig.x2 !== undefined) {
      this.lineX2.value = lineConfig.x2;
      document.getElementById('lineX2Value').textContent = lineConfig.x2;
    }
    if (lineConfig.y2 !== undefined) {
      this.lineY2.value = lineConfig.y2;
      document.getElementById('lineY2Value').textContent = lineConfig.y2;
    }
    if (lineConfig.tolerance !== undefined) {
      this.lineTolerance.value = lineConfig.tolerance;
      document.getElementById('lineToleranceValue').textContent = lineConfig.tolerance;
    }
    if (lineConfig.color) this.lineColor.value = lineConfig.color;
    if (lineConfig.thickness !== undefined) {
      this.lineThickness.value = lineConfig.thickness;
      document.getElementById('lineThicknessValue').textContent = lineConfig.thickness;
    }
    if (lineConfig.show_line !== undefined) this.showLine.checked = lineConfig.show_line;
    if (lineConfig.show_counts !== undefined) this.showCounts.checked = lineConfig.show_counts;
  }

  applyDefaultConfig() {
    this.streams = [industrialMonitor.createStreamConfig({}, 0)];
    this.activeStreamId = this.streams[0].id;
    this.renderStreamTabs();
    this.applyStreamToForm(this.streams[0]);
    this.streamsInitialized = true;
    this.updateStreamCount();

    this.confidence.value = '0.25';
    document.getElementById('confValue').textContent = '0.25';
    this.maxDetections.value = '300';
    document.getElementById('maxDetValue').textContent = '300';
    this.showBox.checked = true;
    this.tracking.checked = true;
    this.showTrail.checked = true;
    this.trailConfig.style.display = 'block';
    this.trailLength.value = '50';
    document.getElementById('trailLengthValue').textContent = '50';
    this.trailThickness.value = '2';
    document.getElementById('trailThicknessValue').textContent = '2';

    this.lineCrossingEnabled.checked = false;
    this.lineCrossingConfig.style.display = 'none';
    this.lineDirection.value = 'horizontal';
    this.lineX1.value = '100';
    document.getElementById('lineX1Value').textContent = '100';
    this.lineY1.value = '300';
    document.getElementById('lineY1Value').textContent = '300';
    this.lineX2.value = '800';
    document.getElementById('lineX2Value').textContent = '800';
    this.lineY2.value = '300';
    document.getElementById('lineY2Value').textContent = '300';
    this.lineTolerance.value = '5';
    document.getElementById('lineToleranceValue').textContent = '5';
    this.lineColor.value = 'green';
    this.lineThickness.value = '3';
    document.getElementById('lineThicknessValue').textContent = '3';
    this.showLine.checked = true;
    this.showCounts.checked = true;

    this.updateConfigPreview();
  }

  async startMonitor() {
    const enabledStreams = this.streams.filter((stream) => stream.enabled !== false);
    if (enabledStreams.length === 0) {
      industrialMonitor.showNotification('至少需要启用一个监控流', 'error');
      return;
    }

    const payload = this.buildSavePayload();
    try {
      await industrialMonitor.request('/appConfigs', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      if (payload.line_crossing && payload.line_crossing.enabled) {
        await industrialMonitor.request('/line/config', {
          method: 'POST',
          body: JSON.stringify(payload.line_crossing),
        });
      }
      industrialMonitor.storage.set('appConfig', payload);
      industrialMonitor.showNotification('配置已保存，正在启动监控...', 'success');
      window.location.href = 'index.html';
    } catch (error) {
      console.error('保存配置失败:', error);
      industrialMonitor.showNotification('保存配置失败，但将继续启动监控', 'warning');
      industrialMonitor.storage.set('appConfig', payload);
      window.location.href = 'index.html';
    }
  }

  startTimeUpdate() {
    this.updateCurrentTime();
    setInterval(() => this.updateCurrentTime(), 1000);
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
    this.currentTimeElement.textContent = `🕐 ${timeString}`;
  }

  async loadSavedConfig() {
    try {
      const response = await industrialMonitor.request('/appConfigs');
      const config = response || {};
      try {
        const lineConfig = await industrialMonitor.request('/line/config');
        if (lineConfig && lineConfig.enabled) {
          config.line_crossing = lineConfig;
        }
      } catch (error) {
        console.warn('加载绊线配置失败:', error);
      }

      if (Object.keys(config).length > 0) {
        this.applyConfig(config);
        this.configStatusElement.textContent = '已从服务器加载';
      } else {
        const localConfig = industrialMonitor.storage.get('appConfig', {});
        if (Object.keys(localConfig).length > 0) {
          this.applyConfig(localConfig);
          this.configStatusElement.textContent = '已加载本地备份';
        } else {
          this.applyDefaultConfig();
          this.configStatusElement.textContent = '默认配置';
        }
      }
    } catch (error) {
      console.error('加载服务器配置失败:', error);
      const localConfig = industrialMonitor.storage.get('appConfig', {});
      if (Object.keys(localConfig).length > 0) {
        this.applyConfig(localConfig);
        this.configStatusElement.textContent = '已加载本地备份';
      } else {
        this.applyDefaultConfig();
        this.configStatusElement.textContent = '默认配置';
      }
    }
  }
}

let configController;
document.addEventListener('DOMContentLoaded', () => {
  configController = new ConfigController();
});
