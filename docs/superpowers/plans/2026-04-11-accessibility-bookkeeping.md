# 无障碍权限自动记账完整实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现无障碍服务到数据入库的完整链路，修复权限状态 UI，并在通知/无障碍两条路径间做去重合并。

**Architecture:** Java 层两个服务（NLService、AccessibilityService）各自发 Broadcast 并携带 `source` 字段；Python 层 `NotificationHandler` 根据 source 决定调用 `add_transaction`（通知路径）还是 `upsert_transaction`（无障碍路径）；`upsert_transaction` 在 `Database` 层实现 10 秒窗口去重。

**Tech Stack:** Python 3, Kivy/KivyMD, pyjnius, SQLite, Java (Android AccessibilityService / NotificationListenerService), pytest

---

## 文件清单

| 文件 | 操作 | 职责 |
|------|------|------|
| `src/core/database.py` | 修改 | 新增 `upsert_transaction()` |
| `tests/test_database.py` | 修改 | 新增 upsert 相关测试 |
| `src/service/notification_service.py` | 修改 | `handle()` 增加 `source` 参数，区分路径 |
| `tests/test_notification_handler.py` | 修改 | 新增 source 路由和 upsert 集成测试 |
| `src/ui/settings_screen.py` | 修改 | 拆分权限状态显示，新增无障碍权限检测 |
| `src/android/org/example/autobookkeeping/NLService.java` | 修改 | Broadcast 增加 `source=notification` |
| `src/android/org/example/autobookkeeping/AutoBookkeepingAccessibilityService.java` | 修改 | Broadcast 增加 `source=accessibility` |
| `src/res/xml/accessibility_service_config.xml` | 修改 | description 改为 `@string/accessibility_desc` |
| `src/res/values/strings.xml` | 修改 | 补充 `app_name` 字段 |

---

## Task 1: Database — upsert_transaction()

**Files:**
- Modify: `src/core/database.py`
- Test: `tests/test_database.py`

- [ ] **Step 1: 写失败测试**

在 `tests/test_database.py` 末尾追加：

```python
def test_upsert_transaction_updates_existing_within_window():
    """无障碍数据在 10s 内到达，应更新已有记录而非新增"""
    db = make_db()
    # 通知路径先插入
    t1 = sample_transaction(
        amount=25.50, type='expense', merchant='未知',
        source='notification', created_at='2026-04-11T10:00:00', pending=0
    )
    tid = db.add_transaction(t1)

    # 无障碍路径 5 秒后到达，同金额同类型
    t2 = sample_transaction(
        amount=25.50, type='expense', merchant='麦当劳',
        source='accessibility', created_at='2026-04-11T10:00:05', pending=0
    )
    result_id = db.upsert_transaction(t2, window_seconds=10)

    # 应返回原记录 id，且商家已更新
    assert result_id == tid
    updated = db.get_transaction(tid)
    assert updated.merchant == '麦当劳'
    assert updated.source == 'accessibility'
    # 总记录数仍为 1
    assert len(db.get_transactions()) == 1


def test_upsert_transaction_inserts_when_no_match():
    """无障碍数据在窗口外，或金额不同，应新增记录"""
    db = make_db()
    t1 = sample_transaction(
        amount=25.50, type='expense', merchant='未知',
        source='notification', created_at='2026-04-11T10:00:00', pending=0
    )
    db.add_transaction(t1)

    # 15 秒后到达，超出窗口
    t2 = sample_transaction(
        amount=25.50, type='expense', merchant='麦当劳',
        source='accessibility', created_at='2026-04-11T10:00:15', pending=0
    )
    result_id = db.upsert_transaction(t2, window_seconds=10)

    assert result_id != db.get_transactions()[1].id or len(db.get_transactions()) == 2
    assert len(db.get_transactions()) == 2


def test_upsert_transaction_does_not_merge_different_amounts():
    """金额不同的两条记录不应合并"""
    db = make_db()
    t1 = sample_transaction(
        amount=25.50, type='expense', merchant='未知',
        source='notification', created_at='2026-04-11T10:00:00', pending=0
    )
    db.add_transaction(t1)

    t2 = sample_transaction(
        amount=30.00, type='expense', merchant='星巴克',
        source='accessibility', created_at='2026-04-11T10:00:03', pending=0
    )
    db.upsert_transaction(t2, window_seconds=10)

    assert len(db.get_transactions()) == 2
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd /Users/l/Desktop/Automatic-bookkeeping
python -m pytest tests/test_database.py::test_upsert_transaction_updates_existing_within_window tests/test_database.py::test_upsert_transaction_inserts_when_no_match tests/test_database.py::test_upsert_transaction_does_not_merge_different_amounts -v
```

预期：`AttributeError: 'Database' object has no attribute 'upsert_transaction'`

- [ ] **Step 3: 实现 `upsert_transaction()`**

在 `src/core/database.py` 的 `delete_transaction` 方法之后、`get_pending_transactions` 之前插入：

```python
def upsert_transaction(self, t: Transaction, window_seconds: int = 10) -> int:
    row = self.conn.execute(
        """SELECT id FROM transactions
           WHERE amount = ? AND type = ?
             AND ABS(CAST(strftime('%s', created_at) AS INTEGER)
                   - CAST(strftime('%s', ?) AS INTEGER)) <= ?
             AND pending = 0
           ORDER BY created_at DESC LIMIT 1""",
        (t.amount, t.type, t.created_at, window_seconds)
    ).fetchone()

    if row:
        self.conn.execute(
            "UPDATE transactions SET merchant=?, source=? WHERE id=?",
            (t.merchant, t.source, row['id'])
        )
        self.conn.commit()
        return row['id']
    else:
        return self.add_transaction(t)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest tests/test_database.py -v
```

预期：所有测试 PASS

- [ ] **Step 5: 提交**

```bash
git add src/core/database.py tests/test_database.py
git commit -m "feat: add upsert_transaction with 10s dedup window"
```

---

## Task 2: NotificationHandler — source 路由

**Files:**
- Modify: `src/service/notification_service.py`
- Test: `tests/test_notification_handler.py`

- [ ] **Step 1: 写失败测试**

在 `tests/test_notification_handler.py` 末尾追加：

```python
def test_handle_accessibility_source_upserts(handler):
    """无障碍来源应调用 upsert，合并 10s 内同金额记录"""
    # 先用通知路径插入一条
    handler.handle(
        'com.eg.android.AlipayGphone',
        '支付宝消息支出 25.50元 商家：未知',
        posted_at='2026-04-11T10:00:00',
        source='notification'
    )
    assert len(handler.db.get_transactions()) == 1

    # 无障碍路径 3 秒后到达
    handler.handle(
        'com.eg.android.AlipayGphone',
        '收款方\n麦当劳\n25.50\n支付成功',
        posted_at='2026-04-11T10:00:03',
        source='accessibility'
    )
    txns = handler.db.get_transactions()
    # 仍只有 1 条记录
    assert len(txns) == 1
    # 商家已更新
    assert txns[0].merchant == '麦当劳'
    assert txns[0].source == 'accessibility'


def test_handle_notification_source_always_inserts(handler):
    """通知来源始终新增，不做 upsert"""
    handler.handle(
        'com.eg.android.AlipayGphone',
        '支付宝消息支出 25.50元 商家：麦当劳',
        posted_at='2026-04-11T10:00:00',
        source='notification'
    )
    handler.handle(
        'com.eg.android.AlipayGphone',
        '支付宝消息支出 25.50元 商家：麦当劳',
        posted_at='2026-04-11T10:00:02',
        source='notification'
    )
    assert len(handler.db.get_transactions()) == 2


def test_handle_default_source_is_notification(handler):
    """不传 source 时默认走通知路径（始终 insert）"""
    handler.handle(
        'com.eg.android.AlipayGphone',
        '支付宝消息支出 10.00元 商家：测试'
    )
    txns = handler.db.get_transactions()
    assert len(txns) == 1
    assert txns[0].source in ('alipay', 'wechat', 'notification', 'manual')
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/test_notification_handler.py::test_handle_accessibility_source_upserts tests/test_notification_handler.py::test_handle_notification_source_always_inserts tests/test_notification_handler.py::test_handle_default_source_is_notification -v
```

预期：`TypeError: handle() got an unexpected keyword argument 'source'`

- [ ] **Step 3: 修改 `NotificationHandler.handle()`**

将 `src/service/notification_service.py` 中 `handle` 方法签名和入库逻辑改为：

```python
def handle(self, package_name: str, text: str, posted_at: Optional[str] = None, source: str = 'notification') -> bool:
    from src.models.transaction import Transaction

    timestamp = posted_at or datetime.now().isoformat(timespec='seconds')
    result = self._parse(package_name, text)

    if result is None:
        t = Transaction(
            id=None,
            amount=0.0,
            type='expense',
            category_id=None,
            merchant='未知',
            note=text[:200],
            source=package_name,
            created_at=timestamp,
            pending=1
        )
        self.db.add_transaction(t)
        logger.info(f"Unrecognized notification saved as pending: {text[:50]}")
        return False

    categories = self.db.get_categories()
    category_id = self._categorize(result.merchant, categories)

    t = Transaction(
        id=None,
        amount=result.amount,
        type=result.type,
        category_id=category_id,
        merchant=result.merchant,
        note='',
        source=source if source == 'accessibility' else result.source,
        created_at=timestamp,
        pending=0
    )

    if source == 'accessibility':
        self.db.upsert_transaction(t)
    else:
        self.db.add_transaction(t)

    logger.info(f"Transaction saved: {result.type} {result.amount} from {result.merchant}")
    return True
```

- [ ] **Step 4: 运行全部 handler 测试**

```bash
python -m pytest tests/test_notification_handler.py -v
```

预期：所有测试 PASS

- [ ] **Step 5: 提交**

```bash
git add src/service/notification_service.py tests/test_notification_handler.py
git commit -m "feat: route accessibility source to upsert_transaction"
```

---

## Task 3: BroadcastReceiver — 传递 source 字段

**Files:**
- Modify: `src/service/notification_service.py`（`MyBroadcastReceiver.ReceiverCallback.onReceive`）
- Modify: `src/android/org/example/autobookkeeping/NLService.java`
- Modify: `src/android/org/example/autobookkeeping/AutoBookkeepingAccessibilityService.java`

> 注：Java 层改动无法在桌面运行单元测试，通过代码审查验证。

- [ ] **Step 1: 修改 `NLService.java`，Broadcast 增加 source**

将 `src/android/org/example/autobookkeeping/NLService.java` 中发送 Intent 的部分改为：

```java
Intent intent = new Intent("org.example.autobookkeeping.NOTIFICATION");
intent.putExtra("package", packageName);
intent.putExtra("text", fullText);
intent.putExtra("source", "notification");
sendBroadcast(intent);
```

- [ ] **Step 2: 修改 `AutoBookkeepingAccessibilityService.java`，Broadcast 增加 source**

将 `src/android/org/example/autobookkeeping/AutoBookkeepingAccessibilityService.java` 中发送 Intent 的部分改为：

```java
Intent intent = new Intent("org.example.autobookkeeping.ACCESSIBILITY");
intent.putExtra("package", packageName);
intent.putExtra("text", combinedText);
intent.putExtra("source", "accessibility");
sendBroadcast(intent);
```

- [ ] **Step 3: 修改 Python BroadcastReceiver 读取 source**

在 `src/service/notification_service.py` 的 `ReceiverCallback.onReceive` 方法中，读取 `source` extra 并传给 `handle()`：

```python
@java_method('(Landroid/content/Context;Landroid/content/Intent;)V')
def onReceive(self, context, intent):
    package = intent.getStringExtra('package')
    text = intent.getStringExtra('text')
    source = intent.getStringExtra('source') or 'notification'
    if package and text:
        self.handler.handle(package, text, source=source)
```

- [ ] **Step 4: 运行现有测试确认无回归**

```bash
python -m pytest tests/ -v
```

预期：所有测试 PASS

- [ ] **Step 5: 提交**

```bash
git add src/service/notification_service.py \
        src/android/org/example/autobookkeeping/NLService.java \
        src/android/org/example/autobookkeeping/AutoBookkeepingAccessibilityService.java
git commit -m "feat: pass source extra in broadcasts, read in Python receiver"
```

---

## Task 4: Settings UI — 拆分权限状态显示

**Files:**
- Modify: `src/ui/settings_screen.py`

> 注：UI 改动在桌面环境下权限检测始终返回 True（非 Android），通过视觉检查验证布局。

- [ ] **Step 1: 新增 `_check_accessibility_permission()` 方法**

在 `src/ui/settings_screen.py` 的 `_check_notification_permission` 方法之后插入：

```python
def _check_accessibility_permission(self):
    from kivy.utils import platform
    if platform == 'android':
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            context = PythonActivity.mActivity.getApplicationContext()
            Settings = autoclass('android.provider.Settings')
            enabled = Settings.Secure.getString(
                context.getContentResolver(),
                Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
            )
            return bool(enabled and 'AutoBookkeepingAccessibilityService' in enabled)
        except Exception:
            return False
    return True
```

- [ ] **Step 2: 拆分权限区域 UI**

将 `_build_ui` 中权限区域（`perm_box` 相关代码）替换为两行独立显示：

```python
root.add_widget(MDLabel(text='系统权限管理 (必需)', size_hint_y=None, height='40dp'))

# 通知权限行
notif_row = MDBoxLayout(orientation='horizontal', size_hint_y=None, height='48dp', spacing='12dp')
self.notif_status_label = MDLabel(text="通知权限：检测中", markup=True, size_hint_x=0.5)
notif_row.add_widget(self.notif_status_label)
notif_row.add_widget(MDRaisedButton(
    text='去授权',
    theme_text_color='Custom', text_color=(0, 0, 0, 1),
    on_release=lambda x: self._open_notification_settings()
))
root.add_widget(notif_row)

# 无障碍权限行
acc_row = MDBoxLayout(orientation='horizontal', size_hint_y=None, height='48dp', spacing='12dp')
self.acc_status_label = MDLabel(text="无障碍权限：检测中", markup=True, size_hint_x=0.5)
acc_row.add_widget(self.acc_status_label)
acc_row.add_widget(MDRaisedButton(
    text='去授权',
    theme_text_color='Custom', text_color=(0, 0, 0, 1),
    on_release=lambda x: self._open_accessibility_settings()
))
root.add_widget(acc_row)
```

同时删除原来的 `perm_box` 和 `self.perm_status_label` 相关代码。

- [ ] **Step 3: 更新 `_update_permission_status()`**

将原方法替换为：

```python
def _update_permission_status(self):
    has_notif = self._check_notification_permission()
    self.notif_status_label.text = (
        "通知权限：[color=00CC00]已授权[/color]" if has_notif
        else "通知权限：[color=FF3333]未授权[/color]"
    )
    has_acc = self._check_accessibility_permission()
    self.acc_status_label.text = (
        "无障碍权限：[color=00CC00]已授权[/color]" if has_acc
        else "无障碍权限：[color=FF3333]未授权[/color]"
    )
```

- [ ] **Step 4: 运行现有测试确认无回归**

```bash
python -m pytest tests/ -v
```

预期：所有测试 PASS

- [ ] **Step 5: 提交**

```bash
git add src/ui/settings_screen.py
git commit -m "feat: split permission status UI, add accessibility permission check"
```

---

## Task 5: 修复配置文件

**Files:**
- Modify: `src/res/xml/accessibility_service_config.xml`
- Modify: `src/res/values/strings.xml`

- [ ] **Step 1: 修正 `accessibility_service_config.xml` 的 description 引用**

将 `src/res/xml/accessibility_service_config.xml` 中：

```xml
android:description="@string/app_name"
```

改为：

```xml
android:description="@string/accessibility_desc"
```

- [ ] **Step 2: 补充 `strings.xml` 的 `app_name` 字段**

将 `src/res/values/strings.xml` 改为：

```xml
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">自动记账</string>
    <string name="accessibility_desc">自动记账辅助服务：用于检测支付成功页面并读取金额</string>
</resources>
```

- [ ] **Step 3: 提交**

```bash
git add src/res/xml/accessibility_service_config.xml src/res/values/strings.xml
git commit -m "fix: correct accessibility_service_config description ref, add app_name string"
```

---

## Task 6: 端到端验证

- [ ] **Step 1: 运行全部测试**

```bash
python -m pytest tests/ -v
```

预期：所有测试 PASS，无 warning

- [ ] **Step 2: 手动验证模拟流程（桌面）**

启动 App 后进入设置页，确认：
- 通知权限和无障碍权限各自独立显示一行
- 桌面环境下两个权限均显示"已授权"（绿色）
- 点击"模拟支付宝支出"后首页出现新记录

- [ ] **Step 3: 最终提交**

```bash
git add -A
git status  # 确认无意外文件
git commit -m "chore: complete accessibility bookkeeping end-to-end implementation"
```
