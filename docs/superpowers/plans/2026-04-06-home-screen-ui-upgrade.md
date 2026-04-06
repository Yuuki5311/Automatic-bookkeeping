# Home Screen UI Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 升级首页 UI，将摘要区域改为橙色圆角卡片，将账单列表行改为独立白底卡片样式。

**Architecture:** 仅修改 `src/ui/home_screen.py`，用 `MDCard` 替换 `MDBoxLayout` 实现摘要卡片和账单行卡片，保持现有数据逻辑和交互逻辑不变。

**Tech Stack:** Python, KivyMD (`MDCard`, `MDLabel`, `MDBoxLayout`, `MDScrollView`)

---

## File Map

- Modify: `src/ui/home_screen.py` — 首页屏幕，包含摘要卡片和账单列表

---

### Task 1: 升级摘要卡片为橙色 MDCard

**Files:**
- Modify: `src/ui/home_screen.py`

- [ ] **Step 1: 在 `_build_ui` 中替换 summary_box**

将 `home_screen.py` 的 `_build_ui` 方法中的 `summary_box` 部分替换为以下代码：

```python
from kivymd.uix.card import MDCard

# 摘要卡片
summary_card = MDCard(
    orientation='horizontal',
    size_hint_y=None,
    height='100dp',
    padding='16dp',
    radius=[12, 12, 12, 12],
    elevation=0,
)
# 延迟设置背景色（需要 App 实例已初始化）
from kivy.clock import Clock
Clock.schedule_once(lambda dt: setattr(
    summary_card, 'md_bg_color',
    summary_card.theme_cls.primary_color
), 0)

left_col = MDBoxLayout(orientation='vertical')
self.income_label = MDLabel(
    text='本月收入',
    theme_text_color='Custom',
    text_color=(1, 1, 1, 0.85),
    font_style='Caption',
    halign='center',
)
self.income_amount = MDLabel(
    text='¥0.00',
    theme_text_color='Custom',
    text_color=(1, 1, 1, 1),
    font_style='H6',
    halign='center',
)
left_col.add_widget(self.income_label)
left_col.add_widget(self.income_amount)

right_col = MDBoxLayout(orientation='vertical')
self.expense_label = MDLabel(
    text='本月支出',
    theme_text_color='Custom',
    text_color=(1, 1, 1, 0.85),
    font_style='Caption',
    halign='center',
)
self.expense_amount = MDLabel(
    text='¥0.00',
    theme_text_color='Custom',
    text_color=(1, 1, 1, 1),
    font_style='H6',
    halign='center',
)
right_col.add_widget(self.expense_label)
right_col.add_widget(self.expense_amount)

summary_card.add_widget(left_col)
summary_card.add_widget(right_col)
root.add_widget(summary_card)
```

- [ ] **Step 2: 更新 `refresh()` 中的摘要数据绑定**

将 `refresh()` 中原来更新 `income_label.text` / `expense_label.text` 的两行改为：

```python
self.income_label.text = '本月收入'
self.income_amount.text = f"¥{summary['income']:.2f}"
self.expense_label.text = '本月支出'
self.expense_amount.text = f"¥{summary['expense']:.2f}"
```

- [ ] **Step 3: 确认无语法错误**

在终端运行：
```bash
python -c "import ast; ast.parse(open('src/ui/home_screen.py').read()); print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add src/ui/home_screen.py
git commit -m "feat: upgrade summary area to orange MDCard"
```

---

### Task 2: 升级账单列表行为白底 MDCard

**Files:**
- Modify: `src/ui/home_screen.py`

- [ ] **Step 1: 替换 `refresh()` 中的账单行构建逻辑**

将 `refresh()` 中 `for t in transactions:` 循环体替换为：

```python
for t in transactions:
    cat = categories.get(t.category_id)
    cat_name = cat.name if cat else '未分类'
    amount_str = f"{'−' if t.type == 'expense' else '+'} ¥{t.amount:.2f}"
    time_str = t.created_at[:10] if t.created_at else ''
    amount_color = (0.9, 0.2, 0.2, 1) if t.type == 'expense' else (0.2, 0.7, 0.2, 1)

    card = MDCard(
        orientation='horizontal',
        size_hint_y=None,
        height='72dp',
        padding='12dp',
        radius=[8, 8, 8, 8],
        elevation=1,
        md_bg_color=(1, 1, 1, 1),
    )

    # 左侧：商家名 + 分类名
    left = MDBoxLayout(orientation='vertical', size_hint_x=0.65)
    left.add_widget(MDLabel(
        text=t.merchant,
        size_hint_y=0.55,
        shorten=True,
        shorten_from='right',
    ))
    left.add_widget(MDLabel(
        text=cat_name,
        size_hint_y=0.45,
        theme_text_color='Custom',
        text_color=(0.6, 0.6, 0.6, 1),
        font_style='Caption',
    ))

    # 右侧：金额 + 日期
    right = MDBoxLayout(orientation='vertical', size_hint_x=0.35)
    right.add_widget(MDLabel(
        text=amount_str,
        theme_text_color='Custom',
        text_color=amount_color,
        halign='right',
        size_hint_y=0.55,
        font_style='Subtitle2',
    ))
    right.add_widget(MDLabel(
        text=time_str,
        theme_text_color='Custom',
        text_color=(0.6, 0.6, 0.6, 1),
        halign='right',
        size_hint_y=0.45,
        font_style='Caption',
    ))

    card.add_widget(left)
    card.add_widget(right)

    tid = t.id
    card.bind(on_touch_down=lambda inst, touch, _id=tid:
        self._on_row_touch(inst, touch, _id))
    self.transaction_list.add_widget(card)
```

- [ ] **Step 2: 将 transaction_list 的 spacing 改为 8dp**

在 `_build_ui` 中找到 `self.transaction_list = MDBoxLayout(...)` 这行，将 `spacing='2dp'` 改为 `spacing='8dp'`，并加上 `padding='8dp'`：

```python
self.transaction_list = MDBoxLayout(
    orientation='vertical',
    size_hint_y=None,
    spacing='8dp',
    padding=[8, 8, 8, 8],
)
```

- [ ] **Step 3: 确认无语法错误**

```bash
python -c "import ast; ast.parse(open('src/ui/home_screen.py').read()); print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add src/ui/home_screen.py
git commit -m "feat: upgrade transaction rows to white MDCard style"
```

---

### Task 3: 确认 MDCard import 已添加

**Files:**
- Modify: `src/ui/home_screen.py`

- [ ] **Step 1: 检查文件顶部 import**

确认 `home_screen.py` 顶部有以下 import（如果 Task 1 已加则跳过）：

```python
from kivymd.uix.card import MDCard
```

如果没有，在现有 import 块末尾添加这一行。

- [ ] **Step 2: 最终语法检查**

```bash
python -c "import ast; ast.parse(open('src/ui/home_screen.py').read()); print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit（如有改动）**

```bash
git add src/ui/home_screen.py
git commit -m "fix: ensure MDCard import in home_screen"
```
