# 轨迹追踪功能使用说明

## 功能概述

本功能在现有的YOLO目标检测和追踪基础上，增加了轨迹线绘制功能，可以显示目标的移动轨迹。

## 新增参数

### 轨迹显示参数

- `show_trail`: 是否显示轨迹线 (0/1)
- `trail_length`: 轨迹最大长度 (默认50)
- `trail_thickness`: 轨迹线粗细 (默认2)
- `trail_color`: 轨迹线颜色 (可选，默认自动生成)

### 检测框显示参数

- `show_box`: 是否显示检测框 (0/1)
- `box_color`: 检测框颜色 (可选，默认YOLO内置颜色)

## 使用方法

### 1. 基本轨迹追踪

启用追踪和轨迹线显示：

```
http://localhost:8080/stream?track=1&show_trail=1
```

### 2. 自定义轨迹参数

```
http://localhost:8080/stream?track=1&show_trail=1&trail_length=30&trail_thickness=3
```

### 3. 完整参数示例

```
http://localhost:8080/stream?src=rtsp://192.168.1.100:554/stream&model_id=80-object-detect&track=1&show_trail=1&trail_length=50&trail_thickness=2&trail_color=red&show_box=1&box_color=green&conf=0.5&fps=30
```

## API接口

### 清理轨迹历史

```
GET /track/clear
```

清理所有轨迹历史数据。

### 获取轨迹统计

```
GET /track/stats
```

返回轨迹统计信息：
```json
{
  "success": true,
  "data": {
    "active_tracks": 5,
    "total_points": 150,
    "max_track_length": 30,
    "track_ids": [1, 2, 3, 4, 5]
  },
  "message": "轨迹统计获取成功"
}
```

## 技术实现

### 轨迹数据结构

```python
track_history = {
    track_id: [(center_x, center_y), (center_x, center_y), ...],
    ...
}
```

### 核心功能

1. **轨迹更新**: 每帧计算目标中心点，添加到对应ID的轨迹历史
2. **轨迹绘制**: 使用OpenCV的polylines绘制轨迹线
3. **颜色生成**: 基于track_id自动生成唯一颜色
4. **检测框绘制**: 支持自定义颜色的检测框绘制
5. **内存管理**: 限制轨迹长度，防止内存溢出

### 性能优化

- 轨迹长度限制：默认50个点
- 自动颜色生成：避免手动设置颜色
- 内存清理：提供清理API

## 注意事项

1. 轨迹功能需要同时启用 `track=1` 和 `show_trail=1`
2. 轨迹线只在有检测结果时绘制
3. 轨迹历史是全局共享的，所有客户端共享同一份数据
4. 建议定期清理轨迹历史以释放内存

## 故障排除

### 轨迹不显示
- 检查是否启用了 `track=1`
- 检查是否启用了 `show_trail=1`
- 确认模型支持追踪功能

### 性能问题
- 减少 `trail_length` 参数
- 降低视频帧率
- 定期调用 `/track/clear` 清理历史

### 内存占用过高
- 调用 `/track/clear` 清理轨迹历史
- 减少 `trail_length` 参数
- 重启服务 