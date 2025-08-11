import logging
import os
import time
import json
import traceback
import cv2
import numpy as np
import subprocess
import env_helper
from PIL import Image

import io
def jpg(frame, quality=100):
    # 转换OpenCV BGR格式为RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # 使用Pillow保存为JPEG字节流
    img = Image.fromarray(rgb_frame)
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=quality, optimize=True)
    return img_bytes.getvalue()



def list_freecam():
    """
    check /dev to find out usb-cam's path
    """
    devices = []
    files = os.listdir("/dev")
    for file in files:
        if file.startswith("video"):
            cap = cv2.VideoCapture("/dev/" + file)
            if cap.isOpened():
                devices.append("/dev/" + file)
                cap.release()
    return devices


def date_now():
    """
    date now in timestamp(ms)
    """
    return int(time.time() * 1000)


def get_jetson_info():
    jetson_info = {
        "product_type": "unknown",
        "ip_address": "unknown",
        "mac_address": "unknown",
        "disk_usage": "-1/-1",
        "cuda_version": "unknown",
        "jetpack_version": "unknown",
        "l4t_version": "unknown",
    }

    try:
        # Get product type
        product_type = (
            subprocess.check_output(["cat", "/sys/firmware/devicetree/base/model"])
            .decode()
            .strip()[:-1]
        )
        jetson_info["product_type"] = product_type
    except Exception as e:
        logging.error(str(e))

    try:
        # Get IP address
        ip_address = (
            subprocess.check_output(["hostname", "-I"]).decode().strip().split(" ")[0]
        )
        jetson_info["ip_address"] = ip_address
    except Exception as e:
        logging.error(str(e))

    try:
        # Get MAC address
        mac_address = (
            subprocess.check_output(["cat", "/sys/class/net/eth0/address"])
            .decode()
            .strip()
        )
        jetson_info["mac_address"] = mac_address
    except Exception as e:
        logging.error(str(e))

    try:
        # Get disk usage
        disk_used_total = (
            os.popen("df / | awk '{print $3,$2}'|sed -n 2p")
            .readline()
            .strip()
            .split(" ")
        )
        disk_usage = "/".join(
            [
                str(int(int(disk_used_total[0]) / 1024)),
                str(int(int(disk_used_total[1]) / 1024)),
            ]
        )
        jetson_info["disk_usage"] = disk_usage
    except Exception as e:
        logging.error(str(e))

    # Get CUDA version
    jetson_info["cuda_version"] = (
        os.popen("nvcc -V |grep 'Cuda compilation tools'|awk '{print $6}'")
        .readline()
        .strip()
    ) or "unknown"

    # Get JetPack version
    jetson_info["jetpack_version"] = (
        os.popen("dpkg-query -l |grep nvidia-vpi |sed -n 1p |awk '{print $3}'")
        .readline()
        .strip()
    ) or "unknown"
    if jetson_info["jetpack_version"] == "unknown":
        jetson_info["jetpack_version"] = (
            os.popen("apt-cache show nvidia-jetpack |grep Version|awk '{print $2}'")
            .readline()
            .strip()
        ) or "unknown"

    # Get L4T version
    jetson_info["l4t_version"] = (
        os.popen("dpkg-query --show nvidia-l4t-core |awk '{print $2}'")
        .readline()
        .strip()
    ) or "unknown"

    return jetson_info


def unpack_tegrastats():
    cmd = "tegrastats | head -n 1"
    info_array = os.popen(cmd).readline().strip().split(" ")
    info = {
        "ram": "-1/-1",
        "swap": "-1/-1",
        "cpu": "-1",
        "gpu": "-1",
        "cpuTemperature": "-1",
        "gpuTemperature": "-1",
    }
    for index, item in enumerate(info_array):
        if item.startswith("CPU@") and item.endswith("C"):
            info["cpuTemperature"] = item.split("@")[1][:-1]
        if item.startswith("GPU@") and item.endswith("C"):
            info["gpuTemperature"] = item.split("@")[1][:-1]
        if item == "GR3D_FREQ":
            info["gpu"] = info_array[index + 1].split("@")[0][:-1]
        if item == "RAM":
            info["ram"] = info_array[index + 1][:-2]
        if item == "SWAP":
            info["swap"] = info_array[index + 1][:-2]
        if item == "CPU":
            cpuCount = 0
            cpuTotalUsage = 0
            for cpuUsage in info_array[index + 1][1:-1].split(","):
                cpuCount += 1
                cpuTotalUsage += float(cpuUsage.split("@")[0][:-1])
            info["cpu"] = str(round(cpuTotalUsage / cpuCount, 2))
    return info


def about_info():
    info = unpack_tegrastats()
    info.update(get_jetson_info())
    info["backend_version"] = env_helper.my_version()
    info["sn"] = "unknown"
    return info
