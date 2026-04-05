# UI 美化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将自动记账 App 改造为温暖柔和风格，包含暖橙主题色、MDCard 卡片布局、美化导航栏、FAB 悬浮按钮。

**Architecture:** 混合方案——用 KivyMD MDCard 包裹列表项，保留现有自定义导航栏结构（避免 MDBottomNavigation 崩溃），通过 theme_cls 设置暖橙主题。不使用 MDDialog（已知崩溃），继续使用 Kivy Popup。

**Tech Stack:** Python 3, Kivy 2.3.0, KivyMD 1.2.0, buildozer, Android API 33, arm64-v8a

---

## 文件结构

| 文件 | 改动内容 |
|------|---------|
| `main.py` | 主题色改 Orange，导航栏高度/图标/高亮，版本号递增到 1.3.0 |
| `src/ui/home_screen.py` | 汇总区改 MDCard，账单列表每行改 MDCard，加 FAB 按钮 |
| `src/ui/stats_screen.py` | 饼图区和柱状图区各用 MDCard 包裹，更新图表颜色 |
| `src/ui/settings_screen.py` | 分类列表每行改 MDCard，移除手动添加账单按钮（移至首页 FAB） |
| `buildozer.spec` | 版本号改为 1.3.0 |

---

### Task 1: 更新主题色和导航栏（main.py）

**Files:**
- Modify: `main.py`
- Modify: `buildozer.spec`

- [ ] **Step 1: 更新 buildozer.spec 版本号**

将 `version = 1.2.5` 改为 `version = 1.3.0`

- [ ] **Step 2: 更新 main.py 主题和导航栏**

将 `main.py` 中 `BookkeepingApp.build()` 方法替换为以下内容：

```python
class BookkeepingApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Orange"
        self.theme_cls.theme_style = "Light"
        _register_chinese_font()

        self.db = Database("bookkeeping.db")
        self.db.init_db()

        root = MDBoxLayout(orientation='vertical')

        self.sm = MDScreenManager()
        self.home_screen = HomeScreen(db=self.db)
        self.stats_screen = StatsScreen(db=self.db)
        self.settings_screen = SettingsScreen(db=self.db)
        self.sm.add_widget(self.home_screen)
        self.sm.add_widget(self.stats_screen)
        self.sm.add_widget(self.settings_screen)
        self.sm.current = 'home'

        # 底部导航栏
        from kivy.graphics import Color, RoundedRectangle
        nav_bar = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height='64dp',
            md_bg_color=self.theme_cls.primary_color,
            padding='4dp',
            spacing='4dp',
        )

        self._nav_btns = {}
        nav_items = [
            ('home', '🏠', '首页'),
            ('stats', '📊', '统计'),
            ('settings', '⚙️', '设置'),
        ]
        for name, icon, label in nav_items:
            btn_box = MDBoxLayout(
                orientation='vertical',
                size_hint_x=0.33,
                padding='4dp',
            )
            icon_lbl = MDLabel(
                text=icon,
                halign='center',
                size_hint_y=None,
                height='28dp',
            )
            text_lbl = MDLabel(
                text=label,
                halign='center',
                size_hint_y=None,
                height='20dp',
                theme_text_color='Custom',
                text_color=(1, 1, 1, 1),
            )
            btn_box.add_widget(icon_lbl)
            btn_box.add_widget(text_lbl)
            btn_box.bind(on_touch_down=lambda inst, touch, n=name:
                self._nav_touch(inst, touch, n))
            nav_bar.add_widget(btn_box)
            self._nav_btns[name] = (btn_box, icon_lbl, text_lbl)

        root.add_widget(self.sm)
        root.add_widget(nav_bar)
        self._update_nav_highlight('home')
        return root

    def _nav_touch(self, instance, touch, name):
        if instance.collide_point(*touch.pos):
            self._switch(name)

    def _update_nav_highlight(self, active_name):
        for name, (box, icon_lbl, text_lbl) in self._nav_btns.items():
            if name == active_name:
                box.md_bg_color = (1, 1, 1, 0.25)
                text_lbl.text_color = (1, 1, 1, 1)
            else:
                box.md_bg_color = (0, 0, 0, 0)
                text_lbl.text_color = (1, 1, 1, 0.7)

    def _switch(self, name):
        self.sm.current = name
        self._update_nav_highlight(name)
        if name == 'home':
            self.home_screen.refresh()
        elif name == 'stats':
            self.stats_screen.refresh()
        elif name == 'settings':
            self.settings_screen.refresh()
```

注意：同时删除旧的 `btn_home`、`btn_stats`、`btn_settings` 相关代码，以及旧的 `_switch` 方法。

- [ ] **Step 3: 提交**

```bash
git add main.py buildozer.spec
git commit -m "feat: update theme to Orange and beautify nav bar"
```

---

### Task 2: 美化首页（home_screen.py）

**Files:**
- Modify: `src/ui/home_screen.py`

- [ ] **Step 1: 更新 imports，加入 MDCard**

在文件顶部 imports 中加入：
```python
from kivymd.uix.card import MDCard
```

- [ ] **Step 2: 替换 `_build_ui` 方法**

```python
def _build_ui(self):
    # 外层用 FloatLayout 支持 FAB 悬浮
    from kivy.uix.floatlayout import FloatLayout
    from kivymd.uix.button import MDFloatingActionButton

    outer = FloatLayout()

    main_box = MDBoxLayout(orientation='vertical', padding='12dp', spacing='12dp')

    # 月度汇总卡片
    summary_card = MDCard(
        orientation='horizontal',
        padding='16dp',
        size_hint_y=None,
        height='100dp',
        radius=[12, 12, 12, 12],
        elevation=2,
        md_bg_color=(1, 1, 1, 1),
    )
    income_box = MDBoxLayout(orientation='vertical')
    self.income_label = MDLabel(
        text='本月收入',
        halign='center',
        theme_text_color='Secondary',
        size_hint_y=None,
        height='30dp',
    )
    self.income_amount = MDLabel(
        text='¥0.00',
        halign='center',
        theme_text_color='Custom',
        text_color=(0.4, 0.74, 0.42, 1),
    )
    income_box.add_widget(self.income_label)
    income_box.add_widget(self.income_amount)

    expense_box = MDBoxLayout(orientation='vertical')
    self.expense_label = MDLabel(
        text='本月支出',
        halign='center',
        theme_text_color='Secondary',
        size_hint_y=None,
        height='30dp',
    )
    self.expense_amount = MDLabel(
        text='¥0.00',
        halign='center',
        theme_text_color='Custom',
        text_color=(1, 0.44, 0.26, 1),
    )
    expense_box.add_widget(self.expense_label)
    expense_box.add_widget(self.expense_amount)

    summary_card.add_widget(income_box)
    summary_card.add_widget(expense_box)
    main_box.add_widget(summary_card)

    scroll = MDScrollView()
    self.transaction_list = MDBoxLayout(
        orientation='vertical',
        size_hint_y=None,
        spacing='8dp',
        padding=[0, 0, 0, '72dp'],
    )
    self.transaction_list.bind(minimum_height=self.transaction_list.setter('height'))
    scroll.add_widget(self.transaction_list)
    main_box.add_widget(scroll)

    outer.add_widget(main_box)

    # FAB 悬浮按钮
    fab = MDFloatingActionButton(
        icon='plus',
        pos_hint={'right': 0.95, 'y': 0.02},
        on_release=lambda x: self._show_add_transaction_popup(),
    )
    outer.add_widget(fab)

    self.add_widget(outer)
```

- [ ] **Step 3: 替换 `refresh` 方法中的汇总标签更新**

将旧的：
```python
self.income_label.text = f"本月收入：¥{summary['income']:.2f}"
self.expense_label.text = f"本月支出：¥{summary['expense']:.2f}"
```
改为：
```python
self.income_amount.text = f"¥{summary['income']:.2f}"
self.expense_amount.text = f"¥{summary['expense']:.2f}"
```

- [ ] **Step 4: 替换账单列表行为 MDCard**

将 `refresh` 方法中的 `row = MDBoxLayout(...)` 部分替换为：

```python
row = MDCard(
    orientation='horizontal',
    size_hint_y=None,
    height='64dp',
    padding='12dp',
    radius=[8, 8, 8, 8],
    elevation=1,
    md_bg_color=(1, 1, 1, 1),
)
```

保留其余内容（MDLabel 子组件、on_touch_down 绑定）不变。

- [ ] **Step 5: 将手动添加账单的弹窗方法从 settings_screen.py 复制到 home_screen.py**

从 `src/ui/settings_screen.py` 中复制 `_show_add_transaction_popup` 和 `_save_transaction` 方法到 `src/ui/home_screen.py`，内容完全相同：

```python
def _show_add_transaction_popup(self):
    content = BoxLayout(orientation='vertical', spacing='8dp', padding='8dp')
    amount_field = MDTextField(hint_text='金额（元）', input_filter='float')
    type_field = MDTextField(hint_text='expense 或 income', text='expense')
    merchant_field = MDTextField(hint_text='商家名称')
    categories = self.db.get_categories()
    cat_field = MDTextField(hint_text=f'分类（{\", \".join(c.name for c in categories)}）')
    note_field = MDTextField(hint_text='备注（可选）')
    for w in [amount_field, type_field, merchant_field, cat_field, note_field]:
        content.add_widget(w)

    popup = Popup(title='手动添加账单', content=content, size_hint=(0.9, 0.85))
    btn_row = BoxLayout(size_hint_y=None, height='48dp', spacing='8dp')
    btn_row.add_widget(MDFlatButton(text='取消', on_release=lambda x: popup.dismiss()))
    btn_row.add_widget(MDRaisedButton(
        text='保存',
        on_release=lambda x: self._save_transaction(
            amount_field.text, type_field.text.strip(),
            merchant_field.text.strip(), cat_field.text.strip(),
            note_field.text.strip(), popup,
        )
    ))
    content.add_widget(btn_row)
    popup.open()

def _save_transaction(self, amount_str, type_str, merchant, cat_name, note, popup):
    from src.models.transaction import Transaction
    try:
        amount = float(amount_str)
    except ValueError:
        return
    if not merchant:
        return
    categories = self.db.get_categories()
    cat_id = next((c.id for c in categories if c.name == cat_name), None)
    if cat_id is None:
        cat_id = next((c.id for c in categories if c.name == '其他'), None)
    t = Transaction(
        id=None, amount=amount,
        type=type_str if type_str in ('income', 'expense') else 'expense',
        category_id=cat_id, merchant=merchant, note=note,
        source='manual',
        created_at=datetime.now().isoformat(timespec='seconds'),
        pending=0,
    )
    self.db.add_transaction(t)
    popup.dismiss()
    self.refresh()
```

同时在 home_screen.py 顶部 imports 加入：
```python
from kivymd.uix.textfield import MDTextField
```

- [ ] **Step 6: 提交**

```bash
git add src/ui/home_screen.py
git commit -m "feat: beautify home screen with MDCard and FAB"
```

---

### Task 3: 美化统计页（stats_screen.py）

**Files:**
- Modify: `src/ui/stats_screen.py`

- [ ] **Step 1: 加入 MDCard import**

在文件顶部加入：
```python
from kivymd.uix.card import MDCard
```

- [ ] **Step 2: 替换 `_build_ui` 方法**

```python
def _build_ui(self):
    scroll = MDScrollView()
    root = MDBoxLayout(orientation='vertical', padding='12dp', spacing='12dp',
                       size_hint_y=None)
    root.bind(minimum_height=root.setter('height'))

    # 饼图卡片
    pie_card = MDCard(
        orientation='vertical',
        padding='12dp',
        size_hint_y=None,
        height='360dp',
        radius=[12, 12, 12, 12],
        elevation=2,
        md_bg_color=(1, 1, 1, 1),
    )
    pie_card.add_widget(MDLabel(
        text='本月支出分类',
        size_hint_y=None,
        height='36dp',
        halign='center',
    ))
    self.pie_chart = PieChart(size_hint_y=None, height='220dp')
    pie_card.add_widget(self.pie_chart)
    self.legend_box = MDBoxLayout(
        orientation='vertical',
        size_hint_y=None,
        height='0dp',
        spacing='4dp',
    )
    pie_card.add_widget(self.legend_box)
    root.add_widget(pie_card)

    # 柱状图卡片
    bar_card = MDCard(
        orientation='vertical',
        padding='12dp',
        size_hint_y=None,
        height='280dp',
        radius=[12, 12, 12, 12],
        elevation=2,
        md_bg_color=(1, 1, 1, 1),
    )
    bar_card.add_widget(MDLabel(
        text='近6个月收支',
        size_hint_y=None,
        height='36dp',
        halign='center',
    ))
    self.bar_chart = BarChart(size_hint_y=None, height='180dp')
    bar_card.add_widget(self.bar_chart)
    legend_bar = MDBoxLayout(orientation='horizontal', size_hint_y=None, height='30dp')
    legend_bar.add_widget(MDLabel(text='■ 收入', theme_text_color='Custom',
                                   text_color=(0.4, 0.74, 0.42, 1), halign='center'))
    legend_bar.add_widget(MDLabel(text='■ 支出', theme_text_color='Custom',
                                   text_color=(1, 0.44, 0.26, 1), halign='center'))
    bar_card.add_widget(legend_bar)
    root.add_widget(bar_card)

    scroll.add_widget(root)
    self.add_widget(scroll)
```

- [ ] **Step 3: 更新 BarChart._draw 中的颜色**

将 `BarChart._draw` 中：
```python
Color(0.2, 0.7, 0.2, 1)
```
改为：
```python
Color(0.4, 0.74, 0.42, 1)
```

将：
```python
Color(0.9, 0.2, 0.2, 1)
```
改为：
```python
Color(1, 0.44, 0.26, 1)
```

- [ ] **Step 4: 更新 refresh 中图例高度计算**

将：
```python
legend_h = len(cat_summary) * 28
self.legend_box.height = str(legend_h) + 'dp'
```
改为：
```python
self.legend_box.height = f"{len(cat_summary) * 28}dp"
pie_card_h = 36 + 220 + len(cat_summary) * 28 + 24 + 12
self.legend_box.parent.height = f"{pie_card_h}dp"
```

注意：`self.legend_box.parent` 即 `pie_card`。

- [ ] **Step 5: 提交**

```bash
git add src/ui/stats_screen.py
git commit -m "feat: beautify stats screen with MDCard"
```

---

### Task 4: 美化设置页（settings_screen.py）

**Files:**
- Modify: `src/ui/settings_screen.py`

- [ ] **Step 1: 加入 MDCard import**

在文件顶部加入：
```python
from kivymd.uix.card import MDCard
```

- [ ] **Step 2: 移除手动添加账单按钮（已移至首页 FAB）**

在 `_build_ui` 方法中，删除以下两行：
```python
root.add_widget(MDLabel(text='手动添加账单', size_hint_y=None, height='40dp'))
root.add_widget(MDRaisedButton(
    text='+ 添加账单', size_hint_y=None, height='48dp',
    on_release=lambda x: self._show_add_transaction_popup(),
))
```

同时删除 `_show_add_transaction_popup` 和 `_save_transaction` 方法（已移至 home_screen.py）。

- [ ] **Step 3: 替换 `refresh` 方法中的分类行为 MDCard**

将 `refresh` 方法中的 `row = MDBoxLayout(...)` 替换为：

```python
row = MDCard(
    orientation='horizontal',
    size_hint_y=None,
    height='64dp',
    padding='12dp',
    radius=[8, 8, 8, 8],
    elevation=1,
    md_bg_color=(1, 1, 1, 1),
)
```

保留其余子组件（MDLabel、MDIconButton）不变。

- [ ] **Step 4: 更新 `_build_ui` 中的间距**

将 `root = MDBoxLayout(orientation='vertical', padding='8dp', spacing='12dp', ...)` 改为：
```python
root = MDBoxLayout(orientation='vertical', padding='12dp', spacing='12dp', size_hint_y=None)
```

- [ ] **Step 5: 提交**

```bash
git add src/ui/settings_screen.py
git commit -m "feat: beautify settings screen with MDCard, move add-transaction to FAB"
```

---

### Task 5: 打包 APK

**Files:**
- No code changes

- [ ] **Step 1: 删除旧 APK**

```bash
rm -f /Users/l/Desktop/Automatic-bookkeeping/bin/*.apk 2>/dev/null; true
```

- [ ] **Step 2: 打包**

```bash
cd /Users/l/Desktop/Automatic-bookkeeping && PATH="$PATH:/Users/l/Library/Python/3.9/bin" /Users/l/Library/Python/3.9/bin/buildozer android debug 2>&1 | tail -20
```

预期输出：`BUILD SUCCESSFUL` 并在 `bin/` 目录生成 `autobookkeeping-1.3.0-arm64-v8a-debug.apk`

- [ ] **Step 3: 确认 APK 存在**

```bash
ls /Users/l/Desktop/Automatic-bookkeeping/bin/*.apk
```

- [ ] **Step 4: 提交最终状态**

```bash
git add buildozer.spec
git commit -m "chore: bump version to 1.3.0 for UI beautification release"
```
