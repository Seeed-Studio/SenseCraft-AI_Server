# 🚀 SenseCraft AI Server - Jetson 部署指南

本指南适用于 **NVIDIA Jetson Ubuntu 22 + JetPack 6.x** 环境，帮助用户快速完成部署。

---

## 📋 环境要求

- **设备**：NVIDIA Jetson 系列（Nano, Xavier, Orin 等）
- **系统**：Ubuntu 22.x + JetPack 6.x
- **网络**：可访问 GitHub 和 Docker Hub
- **权限**：`sudo` 权限

> 如果您的设备未安装合适的系统环境，请参考官方刷机指南进行系统安装和环境准备：
> [JetPack 刷机教程（Seeed Studio）](https://wiki.seeedstudio.com/flash/jetpack_to_selected_product/)

---

## ⚡ 一键部署

在 Jetson 设备终端执行：

```bash
curl -fsSL https://raw.githubusercontent.com/Seeed-Studio/SenseCraft-AI_Server/refs/heads/jetson/scripts/install.sh | bash
```

> 💡 脚本支持 **幂等执行**，可以安全地重复运行。

---

## 🔍 部署流程

> 只是对脚本运行逻辑的简单说明，用户可以无需关注

脚本会自动执行以下步骤：

1. **安装 Docker（27.x）**

   * 检测是否安装 Docker
   * 已安装但不是 27.x → 自动卸载并重新安装
   * 配置 NVIDIA Container Toolkit
   * 将 Docker 默认运行时设置为 `nvidia`

2. **安装 MQTT Broker**

   * 安装 `mosquitto` 和 `mosquitto-clients`
   * 配置允许外部访问：

     ```
     listener 1883 0.0.0.0
     allow_anonymous true
     ```

3. **部署 SenseCraft AI Server**

   * 克隆仓库指定分支到 `~/sensecraft-ai_server`
   * 执行 `scripts/run.sh` 启动服务
   * 下载 YOLOv11 模型到 `~/sensecraft-ai_server/models/yolo11n.pt`

---

## 🛡 异常处理说明

* 本脚本支持 **幂等执行**：

  * **大部分异常**（如网络中断、部分安装失败）只需 **重新运行一次脚本** 即可修复。
  * 脚本会自动检测已安装的软件版本和配置，只安装缺失或错误的部分。
* **少量异常**（如 apt 源永久失效、外部仓库不可访问）需要人工处理。

---

## 🖥 启动与访问

> 脚本会自动启动服务，用户可以无需关注

1. **启动服务**

   ```bash
   cd ~/sensecraft-ai_server
   sudo bash scripts/run.sh
   ```

2. **访问 Web 页面**

   * 浏览器访问：

     ```
     http://<JETSON_IP>:8000
     ```
   * 初次使用请进入 **设置页面**，选择模型和摄像头源，然后保存。

---

## 🛠 常见问题

| 问题                         | 原因                   | 解决方法                                                                                    |
| ---------------------------- | ---------------------- | ------------------------------------------------------------------------------------------- |
| `Docker installation failed` | 网络不稳定 或 源不可用 | 检查网络后重试安装脚本                                                                      |
| Mosquitto 无法连接           | 防火墙或配置错误       | 检查 `/etc/mosquitto/mosquitto.conf` 是否包含 `listener 1883 0.0.0.0`                       |
| YOLO 模型未下载成功          | 网络原因导致下载中断   | 进入~/sensecraft-ai_server/models目录，检查模型文件是否完整，或者删除模型文件，重新运行脚本 |

---

## 📦 卸载服务

```bash
# 卸载 MQTT
sudo apt remove -y mosquitto mosquitto-clients

# 卸载 Docker
sudo apt-get purge -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-ce-rootless-extras

# 删除服务目录
rm -rf ~/sensecraft-ai_server
```

---

## 📚 参考资料

* [Jetson刷机指引文档](https://wiki.seeedstudio.com/flash/jetpack_to_selected_product/)
* [SenseCraft-AI_Server源代码仓库](https://github.com/Seeed-Studio/SenseCraft-AI_Server/tree/jetson)
* [NVIDIA Jetson Docker 指南](https://www.jetson-ai-lab.com/tips_ssd-docker.html)
* [Mosquitto 官方文档](https://mosquitto.org/man/mosquitto-conf-5.html)
