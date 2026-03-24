# Pcmonitor 产品审核报告

## 一、严重问题（必须修复）

### 1. 非 GUI 线程调用 QMessageBox — 程序崩溃风险
- **位置：** `utils/alert_manager.py`
- **问题：** `show_alert_popup()` 从后台线程直接调用 `QMessageBox`，PyQt5 不支持跨线程 UI 操作，会导致随机崩溃
- **方案：** 通过 PyQt5 信号将弹窗请求 marshal 到主线程执行
- **状态：** ✅ 已修复
  - 新增 `popup_requested` 信号，弹窗请求通过信号安全地 marshal 到主线程
  - `trigger_alert` 不再直接调用 `show_alert_popup`，改为 emit `popup_requested` 信号
  - `main_window.py` 中连接 `popup_requested` 信号到 `on_alert_popup_requested` 槽函数
  - 同时修复了告警冷却 key 问题：从 `{type}_{level}` 改为按资源类型冷却，防止 warning↔danger 切换时重置冷却

### 2. 网络监控图表数据解析失败
- **位置：** `ui/monitor_widget.py:103-114`
- **问题：** `extract_numeric_value()` 对网络数据格式 `"↑ 0.50 MB/s | ↓ 0.25 MB/s"` 只能提取到 `0`，导致网络图表始终显示为 0
- **方案：** 为不同类型的监控数据定制解析逻辑，或在数据源端直接传递数值而非格式化字符串
- **状态：** ✅ 已修复
  - `MonitorWidget.update_display()` 现在优先使用独立的 `data_callback` 获取图表数值
  - 新增 `get_network_chart_value()` 方法，将网络总带宽 (上传+下载) 以 100 MB/s 为满量程映射到 0-100
  - 网络 MonitorWidget 构造时传入 `data_callback=self.get_network_chart_value`

### 3. 网络监控初始化阻塞 1 秒
- **位置：** `core/network_monitor.py`
- **问题：** `get_network_speed()` 首次调用时 `time.sleep(1)` 阻塞了 DataCollector 线程，延迟所有监控数据的首次更新
- **方案：** 首次调用返回 0 值，延迟到第二次采集时才计算速度差
- **状态：** ✅ 已修复
  - 首次调用时记录基准值并返回 0，不再 sleep 阻塞

---

## 二、功能缺陷（影响用户体验）

### 4. 历史数据多列永远为 NULL
- **位置：** `utils/database.py` + `core/data_collector.py`
- **问题：** 数据库 schema 包含 `memory_used_gb`、`disk_read_mb`、`disk_write_mb` 等字段，但 DataCollector 从未填充这些值，导致历史记录不完整
- **方案：** 对齐数据采集和数据库 schema，确保所有字段都被正确写入
- **状态：** ✅ 已修复
  - DataCollector 新增磁盘 IO 速率计算 (基于前后两次采样的字节差)
  - `save_history_data` 中 `disk_read_mb` 和 `disk_write_mb` 改为从 `values` 中获取

### 5. 告警冷却机制被绕过
- **位置：** `utils/alert_manager.py:119`
- **问题：** alert_key 格式为 `f"{type}_{level}"`，当 CPU 从 warning→danger→warning 变化时，key 变了，60 秒冷却被重置，用户会收到密集告警
- **方案：** 冷却机制应按**资源类型**（而非 type+level 组合）进行限流
- **状态：** ✅ 已修复 (在 P0 #1 中一并修复)

### 6. 历史图表 X 轴无时间标签
- **位置：** `ui/history_dialog.py`
- **问题：** 折线图 X 轴只显示数据点索引号，用户无法关联峰值对应的时间点
- **方案：** 使用 `DateAxisItem` 或手动设置时间刻度标签
- **状态：** ✅ 已修复
  - CPU 和内存图表改用 `pg.DateAxisItem` 显示时间轴
  - X 轴数据从索引号改为实际 Unix 时间戳

### 7. 颜色代码拼写错误
- **位置：** `ui/history_dialog.py:202`
- **问题：** `'#FF980O'`（字母 O 而非数字 0），导致内存 >70% 时高亮颜色失效
- **方案：** 修正为 `'#FF9800'`
- **状态：** ✅ 已修复

---

## 三、交互设计问题

### 8. 设置页缺少输入校验
- **位置：** `ui/settings_dialog.py`
- **问题：** 告警阈值可以设为不合逻辑的值（如 warning > danger），无任何校验提示
- **方案：** 添加保存前校验：warning 必须 < danger，值必须在 0-100 范围内
- **状态：** ✅ 已修复
  - 新增 `validate_thresholds()` 方法，在 `apply_settings` 前校验所有阈值对

### 9. 进程列表隐性截断
- **位置：** `ui/process_dialog.py`
- **问题：** 最多显示 100 个进程，但 UI 未提示用户列表被截断
- **方案：** 底部显示 `"显示 100 / 共 256 个进程"` 的统计信息
- **状态：** ✅ 已修复
  - 使用 `psutil.pids()` 获取总进程数，状态栏显示 `显示 X / 共 Y 个`

### 10. 无全局日志/错误反馈机制
- **位置：** 所有 `core/` 模块
- **问题：** 大量 bare `except` 静默吞掉异常，监控组件故障时用户完全无感知
- **方案：** 引入 `logging` 模块，关键错误在状态栏或通知区域提示用户
- **状态：** ✅ 已修复
  - `main.py` 初始化 `logging.basicConfig`
  - `core/` 所有模块和 `utils/` 模块添加 `logger`，bare except 改为 `logger.warning/debug`

---

## 四、架构/稳定性问题

### 11. 配置读写线程不安全
- **位置：** `utils/config.py`
- **问题：** `Config.set()` 立即写入文件但无锁保护，DataCollector 并发读取可能导致竞态条件
- **方案：** 给 Config 加 `threading.Lock`
- **状态：** ✅ 已修复
  - Config 新增 `_lock`，`get()`/`set()`/`save_config()` 均加锁保护

### 12. 配置无 schema 校验
- **位置：** `utils/config.py`
- **问题：** config.json 被外部修改后可能包含非法类型（如 `update_interval: "abc"`），直接导致运行时崩溃
- **方案：** 加载时对 key 逐一校验类型和范围
- **状态：** ✅ 已修复
  - 新增 `_validate_config()` 方法，校验类型/范围/阈值逻辑，非法值回退默认
  - `load_config` 异常时使用 `logger.warning` 而非静默忽略

### 13. 数据库持续膨胀
- **位置：** `utils/database.py`
- **问题：** `_cleanup_old_data()` 删除过期记录但从不 `VACUUM`，SQLite 文件只增不减
- **方案：** 定期（如每天一次）执行 `VACUUM`
- **状态：** ✅ 已修复
  - `_cleanup_old_data` 加入 lock 保护和 VACUUM 逻辑（每 100 次清理执行一次）

---

## 五、优先级排序

| 优先级 | 问题编号 | 描述 |
|--------|---------|------|
| **P0 - 立即修复** | #1 | 非 GUI 线程弹窗导致崩溃 |
| **P0 - 立即修复** | #2 | 网络图表数据显示为 0 |
| **P1 - 高优** | #4 | 历史数据字段为空 |
| **P1 - 高优** | #5 | 告警冷却机制失效 |
| **P1 - 高优** | #7 | 颜色代码拼写错误 |
| **P2 - 中优** | #3, #6, #8, #9 | 体验优化类 |
| **P3 - 低优** | #10-#13 | 架构稳定性改进 |

---

## 六、修复进展记录

| 日期 | 问题编号 | 修复内容 | 状态 |
|------|---------|---------|------|
| 2026-03-24 | #1 | 告警弹窗改为信号驱动，确保主线程安全；冷却 key 改为按资源类型 | ✅ 已修复 |
| 2026-03-24 | #2 | 网络图表新增独立 data_callback，正确映射带宽到 0-100 范围 | ✅ 已修复 |
| 2026-03-24 | #5 | 告警冷却 key 从 `{type}_{level}` 改为按资源类型 (在 #1 中一并修复) | ✅ 已修复 |
| 2026-03-24 | #7 | `#FF980O` 修正为 `#FF9800` | ✅ 已修复 |
| 2026-03-24 | #4 | DataCollector 新增磁盘 IO 速率计算，save_history_data 对齐字段映射 | ✅ 已修复 |
| 2026-03-24 | #3 | network_monitor 首次调用返回 0，去掉 time.sleep(1) | ✅ 已修复 |
| 2026-03-24 | #6 | 历史图表改用 DateAxisItem，X 轴显示真实时间 | ✅ 已修复 |
| 2026-03-24 | #8 | settings_dialog 新增 validate_thresholds() 校验阈值逻辑 | ✅ 已修复 |
| 2026-03-24 | #9 | 进程列表状态栏显示 `显示 X / 共 Y 个` 截断提示 | ✅ 已修复 |
| 2026-03-24 | #10 | main.py 初始化 logging，core/utils 全模块添加 logger 替代 bare except | ✅ 已修复 |
| 2026-03-24 | #11 | Config 类新增 threading.Lock，get/set/save 均加锁 | ✅ 已修复 |
| 2026-03-24 | #12 | 新增 _validate_config() 校验配置类型和范围，异常记录日志 | ✅ 已修复 |
| 2026-03-24 | #13 | _cleanup_old_data 加锁 + 每 100 次清理执行 VACUUM | ✅ 已修复 |
| 2026-03-24 | Migration | 项目从 PyQt5 迁移到 PySide6：替换 Qt 导入、Signal、exec()、tray/icon/QMessageBox 兼容点，并升级 requirements 中的 Qt 依赖 | ✅ 代码迁移完成 |
