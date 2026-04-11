# 悬浮窗快捷记账 — 设计文档

日期：2026-04-11

## 背景

微信支付页面使用 FLAG_SECURE 保护，无障碍服务无法读取内容；微信在前台时也不发送系统通知，导致自动记账无法捕获微信支付。悬浮窗提供一个常驻的快捷入口，用户支付完成后立即手动记录，摩擦极低。

## 目标

- 常驻悬浮按钮，随时可用，不遮挡屏幕
- 点击展开完整记账表单（金额、收支类型、商家、分类）
- 提交后显示确认信息 2 秒后自动收起
- 闲置 3 秒后按钮渐变为 30% 透明度

## 架构

### 数据流

```
用户点击悬浮按钮
  → FloatWindowService 展开表单
  → 用户填写并提交
  → 发广播 org.example.autobookkeeping.MANUAL_ENTRY
  → Python MyBroadcastReceiver 接收
  → NotificationHandler.handle() 写入数据库
  → 广播回调显示"已记录 ¥XX.XX"
  → 2 秒后收起回按钮态
```

### 分类数据传递

app 启动时，Python 层读取数据库分类列表，通过广播 `org.example.autobookkeeping.CATEGORIES` 发送给 `FloatWindowService`（JSON 字符串格式）。服务在内存中缓存分类列表，用于填充表单下拉选项。

## 组件

### 新增：`FloatWindowService.java`

- 继承 `Service`，通过 `WindowManager` 管理悬浮窗
- 状态机：`COLLAPSED`（收起）→ `EXPANDED`（展开）→ `CONFIRMED`（确认）→ `COLLAPSED`
- 透明度：收起态静止 3 秒后 alpha 从 1.0 渐变到 0.3；触摸时立即恢复 1.0
- 接收广播：
  - `CATEGORIES` — 更新分类缓存
- 发送广播：
  - `MANUAL_ENTRY` — 携带 amount、type、merchant、category_id

### 修改：`AndroidManifest.tmpl.xml`

- 注册 `FloatWindowService`
- 添加权限 `android.permission.SYSTEM_ALERT_WINDOW`

### 修改：`buildozer.spec`

- `android.permissions` 添加 `SYSTEM_ALERT_WINDOW`

### 修改：`notification_service.py`

- `MyBroadcastReceiver` 的 `IntentFilter` 添加 `MANUAL_ENTRY` action
- `onReceive` 处理 `MANUAL_ENTRY`：直接从 intent extras 读取 amount、type、merchant、category_id 构造 Transaction 写库

### 修改：`settings_screen.py`

- 添加悬浮窗权限检测（`Settings.canDrawOverlays()`）
- 添加"启动悬浮窗"/"停止悬浮窗"按钮，调用 `startService`/`stopService`

## 悬浮窗 UI

### 收起态
- 右侧边缘固定位置，48dp 橙色圆形按钮，显示"记"字
- 可拖动改变垂直位置
- 静止 3 秒后渐变至 30% 透明度

### 展开态
- 点击按钮展开卡片（宽 280dp），包含：
  - 金额输入框（数字键盘）
  - 支出 / 收入切换按钮
  - 商家名称输入框
  - 分类选择（横向滚动按钮组，来自缓存列表）
  - 确认 / 取消按钮
- 始终不透明

### 确认态
- 卡片内显示"已记录 ¥XX.XX"
- 2 秒后自动回到收起态

## 权限

| 权限 | 用途 |
|------|------|
| `SYSTEM_ALERT_WINDOW` | 在其他 app 上方显示悬浮窗 |

用户需在设置中手动授权（`Settings.ACTION_MANAGE_OVERLAY_PERMISSION`），与无障碍权限类似。`settings_screen.py` 中添加检测和跳转按钮。

## 错误处理

- 未授权 `SYSTEM_ALERT_WINDOW`：点击启动按钮时跳转到系统授权页，不启动服务
- 金额为空或非法：确认按钮置灰，不可提交
- 分类列表为空：显示"其他"作为默认选项
