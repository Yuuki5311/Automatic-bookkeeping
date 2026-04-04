# 安卓自动记账工具 — 设计文档

日期：2026-04-04

## 概述

一款运行在 Android 手机上的自动记账 App，通过监听支付宝/微信支付通知自动解析并记录账单，提供账单列表、分类统计和月度报表功能。

技术栈：Python + KivyMD + python-for-android（buildozer 打包 APK）

---

## 架构

```
┌─────────────────────────────────────────┐
│              Android APK                │
│                                         │
│  ┌─────────────┐   ┌─────────────────┐  │
│  │  KivyMD UI  │   │ Notification    │  │
│  │  (主界面)    │   │ Listener Service│  │
│  └──────┬──────┘   └────────┬────────┘  │
│         │                   │           │
│         ▼                   ▼           │
│  ┌─────────────────────────────────┐    │
│  │         业务逻辑层               │    │
│  │  parser.py  │  categorizer.py   │    │
│  └──────────────────┬──────────────┘    │
│                     │                   │
│                     ▼                   │
│  ┌─────────────────────────────────┐    │
│  │       SQLite 数据库              │    │
│  │  transactions / categories      │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

四个层次：
1. **通知监听层** — pyjnius 调用 Android `NotificationListenerService`，监听支付宝/微信通知
2. **解析层** — 正则提取金额、商家、时间、收/支类型
3. **业务层** — 关键词自动分类，写入 SQLite；无法匹配时进入待分类队列
4. **UI 层** — KivyMD 展示账单列表、分类统计、月度报表

---

## 数据库设计

### transactions 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 |
| amount | REAL | 金额（元） |
| type | TEXT | 'income' 或 'expense' |
| category_id | INTEGER | 外键 → categories.id |
| merchant | TEXT | 商家名称 |
| note | TEXT | 备注（可选） |
| source | TEXT | 'alipay' / 'wechat' / 'manual' |
| created_at | TEXT | ISO8601 时间戳 |
| pending | INTEGER | 1=待分类，0=已分类 |

### categories 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 |
| name | TEXT | 分类名称 |
| icon | TEXT | Material Design 图标名 |
| keywords | TEXT | 逗号分隔关键词，用于自动匹配 |

默认分类：餐饮、交通、购物、娱乐、医疗、转账、其他

---

## 通知解析逻辑

### 支付宝

匹配模式：`支付宝消息支出 XX元 商家：XXX`

正则：`支出\s*([\d.]+)元.*?商家[：:]\s*(.+)`

### 微信支付

匹配模式：`微信支付 XX元 收款方：XXX`

正则：`微信支付\s*([\d.]+)元.*?收款方[：:]\s*(.+)`

### 解析流程

1. 收到通知 → 判断来源（支付宝/微信）
2. 正则提取：金额、类型、商家、时间
3. 关键词匹配分类 → 写入 transactions
4. 无法匹配 → `pending=1`，进入待分类队列，通知用户手动确认

---

## UI 设计

底部导航栏 3 个 Tab：

### Tab 1：首页

- 顶部卡片：本月总支出 / 总收入
- 列表：最近流水账（时间倒序）
- 每条账单显示：图标、商家名、分类、金额、时间
- 点击账单 → 详情弹窗（可编辑 / 删除）
- 待分类账单高亮显示，引导用户确认

### Tab 2：统计

- 分类饼图（本月支出按分类占比）
- 月度收支柱状图（近 6 个月）
- 图表库：使用 `kivy_garden.matplotlib` 或内置 Canvas 绘制

### Tab 3：设置

- 通知监听开关（启动/停止 Service）
- 分类管理（增删改分类及关键词）
- 手动添加账单入口

---

## 项目结构

```
Automatic-bookkeeping/
├── main.py                  # App 入口
├── buildozer.spec           # 打包配置
├── src/
│   ├── ui/
│   │   ├── home_screen.py   # 首页
│   │   ├── stats_screen.py  # 统计页
│   │   └── settings_screen.py # 设置页
│   ├── service/
│   │   └── notification_service.py  # 通知监听 Android Service
│   ├── core/
│   │   ├── parser.py        # 通知文本解析
│   │   ├── categorizer.py   # 自动分类
│   │   └── database.py      # SQLite 操作
│   └── models/
│       └── transaction.py   # 数据模型
└── docs/
    └── superpowers/specs/
        └── 2026-04-04-auto-bookkeeping-design.md
```

---

## 关键依赖

| 依赖 | 用途 |
|------|------|
| kivy | UI 框架基础 |
| kivymd | Material Design 组件 |
| pyjnius | 调用 Android Java API |
| buildozer | 打包 APK |
| sqlite3 | 内置，数据存储 |

---

## 权限要求

- `BIND_NOTIFICATION_LISTENER_SERVICE` — 读取通知
- `RECEIVE_BOOT_COMPLETED` — 开机自启监听服务
- `FOREGROUND_SERVICE` — 后台持续运行

---

## 错误处理

- 通知解析失败 → 记入 pending 队列，不丢弃数据
- 数据库写入失败 → 本地日志记录，下次启动重试
- 权限未授予 → 设置页引导用户开启通知访问权限
