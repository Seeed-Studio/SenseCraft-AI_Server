// 公共工具函数和类
class IndustrialMonitor {
  constructor() {
    this.isStreaming = false;
    this.isPaused = false;
    this.currentUrl = '';
    this.currentModelId = null;
    this.sources = [];
    this.models = [];
    this.mqttInterval = null;
    this.isMqttListening = false;
  }

  // 显示通知
  showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 3000);
  }

  // 显示错误信息
  showError(elementId, message) {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
      errorElement.textContent = message;
      errorElement.style.display = 'block';
    }
  }

  // 隐藏错误信息
  hideError(elementId) {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
      errorElement.style.display = 'none';
    }
  }

  // 更新状态指示器
  updateStatus(text, connected) {
    const indicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');

    if (indicator && statusText) {
      statusText.textContent = text;
      indicator.className = 'status-indicator ' + (connected ? 'status-connected' : 'status-disconnected');
    }
  }

  // 显示/隐藏加载状态
  showLoading(show) {
    const loading = document.getElementById('loading');
    if (loading) {
      loading.style.display = show ? 'block' : 'none';
    }
  }

  // 构建流URL
  buildStreamUrl(params = {}) {
    const baseUrl = window.location.origin;
    const urlParams = new URLSearchParams();

    // 合并默认参数和传入参数
    const defaultParams = {
      infering: '1',
      conf: '0.25',
      max_det: '300',
      show_box: '1',
      track: '1',
      show_trail: '1',
      trail_length: '50',
      trail_thickness: '2',
      box_color: 'orange',
      trail_color: 'blue'
    };

    Object.assign(defaultParams, params);

    // 添加所有参数到URL
    Object.entries(defaultParams).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        urlParams.append(key, value);
      }
    });

    return `${baseUrl}/stream?${urlParams.toString()}`;
  }

  // 翻译检测名称
  translateDetectionName(name) {
    const translations = {
      'person': '人',
      'car': '汽车',
      'bicycle': '自行车',
      'dog': '狗',
      'cat': '猫',
      'traffic light': '交通灯',
      'backpack': '背包',
      'handbag': '手提包',
      'truck': '卡车',
      'bus': '公交车',
      'motorcycle': '摩托车',
      'bird': '鸟',
      'horse': '马',
      'sheep': '羊',
      'cow': '牛',
      'elephant': '大象',
      'bear': '熊',
      'zebra': '斑马',
      'giraffe': '长颈鹿'
    };
    return translations[name] || name;
  }

  // 格式化文件大小
  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  // 格式化时间
  formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('zh-CN');
  }

  // 防抖函数
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  // 节流函数
  throttle(func, limit) {
    let inThrottle;
    return function() {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }

  // 本地存储工具
  storage = {
    set: (key, value) => {
      try {
        localStorage.setItem(key, JSON.stringify(value));
      } catch (e) {
        console.error('存储失败:', e);
      }
    },
    
    get: (key, defaultValue = null) => {
      try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
      } catch (e) {
        console.error('读取存储失败:', e);
        return defaultValue;
      }
    },
    
    remove: (key) => {
      try {
        localStorage.removeItem(key);
      } catch (e) {
        console.error('删除存储失败:', e);
      }
    }
  };

  // 网络请求工具
  async request(url, options = {}) {
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
      },
    };

    const finalOptions = { ...defaultOptions, ...options };

    try {
      const response = await fetch(url, finalOptions);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      } else {
        return await response.text();
      }
    } catch (error) {
      console.error('请求失败:', error);
      throw error;
    }
  }

  // 文件上传工具
  async uploadFile(file, endpoint = '/upload', onProgress = null) {
    const formData = new FormData();
    formData.append('file', file);

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      if (onProgress) {
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            onProgress(percentComplete);
          }
        });
      }

      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve(response);
          } catch (e) {
            resolve(xhr.responseText);
          }
        } else {
          reject(new Error(`上传失败: ${xhr.status}`));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('网络错误'));
      });

      xhr.open('POST', endpoint);
      xhr.send(formData);
    });
  }

  // 全屏控制
  toggleFullscreen(element) {
    if (!document.fullscreenElement && !document.webkitFullscreenElement && !document.msFullscreenElement) {
      if (element.requestFullscreen) {
        element.requestFullscreen();
      } else if (element.webkitRequestFullscreen) {
        element.webkitRequestFullscreen();
      } else if (element.msRequestFullscreen) {
        element.msRequestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
      } else if (document.msExitFullscreen) {
        document.msExitFullscreen();
      }
    }
  }

  // 检查全屏状态
  isFullscreen() {
    return !!(document.fullscreenElement || document.webkitFullscreenElement || document.msFullscreenElement);
  }

  // 获取URL参数
  getUrlParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
  }

  // 设置URL参数
  setUrlParam(name, value) {
    const url = new URL(window.location);
    url.searchParams.set(name, value);
    window.history.replaceState({}, '', url);
  }

  // 移除URL参数
  removeUrlParam(name) {
    const url = new URL(window.location);
    url.searchParams.delete(name);
    window.history.replaceState({}, '', url);
  }

  // 复制到剪贴板
  async copyToClipboard(text) {
    try {
      await navigator.clipboard.writeText(text);
      this.showNotification('已复制到剪贴板', 'success');
    } catch (err) {
      console.error('复制失败:', err);
      this.showNotification('复制失败', 'error');
    }
  }

  // 下载文件
  downloadFile(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  // 生成UUID
  generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c == 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  // 验证邮箱格式
  isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  // 验证URL格式
  isValidUrl(string) {
    try {
      new URL(string);
      return true;
    } catch (_) {
      return false;
    }
  }

  // 格式化数字
  formatNumber(num, decimals = 2) {
    return Number(num).toLocaleString('zh-CN', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    });
  }

  // 格式化百分比
  formatPercent(value, total, decimals = 1) {
    if (total === 0) return '0%';
    return ((value / total) * 100).toFixed(decimals) + '%';
  }

  // 深拷贝对象
  deepClone(obj) {
    if (obj === null || typeof obj !== 'object') return obj;
    if (obj instanceof Date) return new Date(obj.getTime());
    if (obj instanceof Array) return obj.map(item => this.deepClone(item));
    if (typeof obj === 'object') {
      const clonedObj = {};
      for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
          clonedObj[key] = this.deepClone(obj[key]);
        }
      }
      return clonedObj;
    }
  }

  // 合并对象
  mergeObjects(...objects) {
    return objects.reduce((result, obj) => {
      return { ...result, ...obj };
    }, {});
  }

  // 数组去重
  uniqueArray(arr, key = null) {
    if (key) {
      const seen = new Set();
      return arr.filter(item => {
        const value = item[key];
        if (seen.has(value)) {
          return false;
        }
        seen.add(value);
        return true;
      });
    } else {
      return [...new Set(arr)];
    }
  }

  // 数组分组
  groupArray(arr, key) {
    return arr.reduce((groups, item) => {
      const group = item[key];
      groups[group] = groups[group] || [];
      groups[group].push(item);
      return groups;
    }, {});
  }

  // 数组排序
  sortArray(arr, key, order = 'asc') {
    return [...arr].sort((a, b) => {
      let aVal = key ? a[key] : a;
      let bVal = key ? b[key] : b;
      
      if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase();
        bVal = bVal.toLowerCase();
      }
      
      if (order === 'desc') {
        return bVal > aVal ? 1 : -1;
      } else {
        return aVal > bVal ? 1 : -1;
      }
    });
  }

  // 延迟执行
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // 重试函数
  async retry(fn, maxAttempts = 3, delayMs = 1000) {
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        return await fn();
      } catch (error) {
        if (attempt === maxAttempts) {
          throw error;
        }
        await this.delay(delayMs * attempt);
      }
    }
  }

  // 事件发射器
  createEventEmitter() {
    const events = {};
    
    return {
      on: (event, callback) => {
        if (!events[event]) {
          events[event] = [];
        }
        events[event].push(callback);
      },
      
      off: (event, callback) => {
        if (events[event]) {
          events[event] = events[event].filter(cb => cb !== callback);
        }
      },
      
      emit: (event, data) => {
        if (events[event]) {
          events[event].forEach(callback => callback(data));
        }
      }
    };
  }
}

// 创建全局实例
window.industrialMonitor = new IndustrialMonitor();

// 导出类（如果使用模块系统）
if (typeof module !== 'undefined' && module.exports) {
  module.exports = IndustrialMonitor;
} 