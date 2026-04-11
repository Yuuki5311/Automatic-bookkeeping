# 无障碍权限自动记账完整实现设计

**日期：** 2026-04-11
**状态：** 已批准

---

## 目标

实现从无障碍权限获取到支付页面数据读取、解析、入库的完整端到端链路，同时修复现有缺口，确保通知路径与无障碍路径数据去重合并。

---

## 现状与缺口

已有：
- `AutoBookkeepingAccessibilityService.java` — 无障碍服务核心逻辑
- `accessibility_service_config.xml` — 服务配置文件
- `AndroidManifest.tmpl.xml` — 服务注册声明
- `settings_screen.py` — 有"无障碍授权"按钮，点击跳转系统设置
- `parser.py` — `_parse_accessibility()` 支持多行文本解析

缺口：
1. `settings_screen.py` 只检查通知权限，未检查无障碍权限状态
2. 两个权限状态混在同一个 label，用户无法区分
3. `accessibility_service_config.xml` 的 `description` 引用了 `@string/app_name`，应改为 `@string/accessibility_desc`
4. `strings.xml` 缺少 `app_name` 字段（Manifest 引用了但未定义）
5. 两条路径同时捕获同一笔交易时无去重机制

---

## 架构

```
支付宝/微信
    │
    ├─[通知栏]─→ NLService.java (source=notification)
    │
    └─[支付页面]─→ AutoBookkeepingAccessibilityService.java (source=accessibility)
                                        │
                            Broadcast Intent（两个 action）
                                        │
                            MyBroadcastReceiver（Python）
                                        │
                            NotificationHandler.handle(source)
                                    │
                            parse_notification()
                                    │
                    ┌───────────────────────────────┐
                    │  source == accessibility?      │
                    │  是 → db.upsert_transaction()  │
                    │  否 → db.add_transaction()     │
                    └───────────────────────────────┘
```

---

## 各模块改动

### 1. `src/android/org/example/autobookkeeping/NLService.java`

发送 Broadcast 时增加 `source` extra：

```java
intent.putExtra("source", "notification");
```

### 2. `src/android/org/example/autobookkeeping/AutoBookkeepingAccessibilityService.java`

发送 Broadcast 时增加 `source` extra：

```java
intent.putExtra("source", "accessibility");
```

### 3. `src/core/database.py`

新增 `upsert_transaction(t, window_seconds=10)`：

- 查找 `window_seconds` 内同金额、同类型、`pending=0` 的记录
- 找到 → UPDATE 该记录的 `merchant` 和 `source` 字段
- 找不到 → 调用 `add_transaction()` 插入新记录
- 返回受影响的记录 id

### 4. `src/service/notification_service.py`

- `MyBroadcastReceiver.ReceiverCallback.onReceive()` 读取 `source` extra 并传给 `handler.handle()`
- `NotificationHandler.handle()` 签名增加 `source` 参数（默认 `'notification'`）
- `source == 'accessibility'` 时调用 `db.upsert_transaction()`，否则调用 `db.add_transaction()`

### 5. `src/ui/settings_screen.py`

- 新增 `_check_accessibility_permission()`：读取 `Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES`，检查是否包含 `AutoBookkeepingAccessibilityService`
- 权限区域拆成两行独立显示：
  ```
  通知权限：[已授权/未授权]  [去授权]
  无障碍权限：[已授权/未授权]  [去授权]
  ```
- `_update_permission_status()` 同步更新两个 label
- 定时刷新（已有 2s interval）覆盖两个权限

### 6. `src/res/xml/accessibility_service_config.xml`

```xml
android:description="@string/accessibility_desc"
```

### 7. `src/res/values/strings.xml`

补充：

```xml
<string name="app_name">自动记账</string>
```

---

## 去重逻辑细节

| 条件 | 行为 |
|------|------|
| 无障碍数据进来，10s 内有同金额同类型记录 | UPDATE merchant、source，不新增 |
| 无障碍数据进来，无匹配记录 | INSERT 新记录 |
| 通知数据进来 | 始终 INSERT（快速响应，先占位） |
| 连续两笔同价交易（>10s 间隔） | 各自独立入库，不误杀 |

时间窗口 10 秒：通知推送到支付页面展示的典型延迟在 1-3 秒，10 秒窗口足够覆盖，同时不会误合并不同交易。

---

## 权限检测实现

**通知权限（已有）：**
- Android 8.1+：`NotificationManager.isNotificationListenerAccessGranted(ComponentName)`
- 降级：读取 `Settings.Secure.enabled_notification_listeners`

**无障碍权限（新增）：**
```python
enabled = Settings.Secure.getString(
    context.getContentResolver(),
    Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
)
return enabled and "AutoBookkeepingAccessibilityService" in enabled
```

---

## 不在本次范围内

- 支付宝/微信以外的 App 支持
- 无障碍数据的 OCR 增强解析
- 去重窗口的用户可配置化
