from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivy.core.text import Label as CoreLabel
from kivymd.uix.scrollview import MDScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Rectangle, Line
from kivy.clock import Clock
from datetime import datetime
import math


class PieChart(Widget):
    """用 Kivy Canvas 绘制饼图"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = []  # list of (label, value, color_rgb)
        self.bind(size=self._draw, pos=self._draw)

    def set_data(self, data):
        """data: list of (label, value, color_rgb)"""
        self.data = data
        self._draw()

    def _draw(self, *args):
        self.canvas.clear()
        if not self.data:
            return

        total = sum(v for _, v, _ in self.data)
        if total == 0:
            return

        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        r = min(self.width, self.height) / 2 * 0.8

        start_angle = 0
        with self.canvas:
            for label, value, color in self.data:
                sweep = 360 * value / total
                Color(*color, 1)
                # Kivy Ellipse angle_start/angle_end in degrees
                Ellipse(
                    pos=(cx - r, cy - r),
                    size=(r * 2, r * 2),
                    angle_start=start_angle,
                    angle_end=start_angle + sweep,
                )
                start_angle += sweep


class BarChart(Widget):
    """用 Kivy Canvas 绘制柱状图（收入绿色，支出红色）"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = []  # list of {'year': int, 'month': int, 'income': float, 'expense': float}
        self.bind(size=self._draw, pos=self._draw)

    def set_data(self, data):
        self.data = data
        self._draw()

    def _draw(self, *args):
        self.canvas.clear()
        if not self.data:
            return

        n = len(self.data)
        max_val = max(
            max(d['income'] for d in self.data),
            max(d['expense'] for d in self.data),
            1  # 避免除零
        )

        padding = 30
        chart_w = self.width - padding * 2
        chart_h = self.height - padding * 2
        bar_group_w = chart_w / n
        bar_w = bar_group_w * 0.35

        with self.canvas:
            for i, d in enumerate(self.data):
                x_base = self.x + padding + i * bar_group_w

                # 收入柱（绿色）
                income_h = (d['income'] / max_val) * chart_h
                Color(0.2, 0.7, 0.2, 1)
                Rectangle(
                    pos=(x_base, self.y + padding),
                    size=(bar_w, income_h)
                )

                # 支出柱（红色）
                expense_h = (d['expense'] / max_val) * chart_h
                Color(0.9, 0.2, 0.2, 1)
                Rectangle(
                    pos=(x_base + bar_w + 2, self.y + padding),
                    size=(bar_w, expense_h)
                )

                # 绘制月份标签
                Color(1, 1, 1, 1)  # 必须设为白色才能正常显示纹理颜色
                lbl = CoreLabel(text=f"{d['month']}月", font_size=12, color=(0.4, 0.4, 0.4, 1), font_name='NotoSansSC-Regular.ttf')
                lbl.refresh()
                tex = lbl.texture
                Rectangle(texture=tex, pos=(x_base + bar_group_w / 2 - tex.size[0] / 2, self.y + padding - 20), size=tex.size)

class StatsScreen(MDScreen):
    # 饼图颜色列表
    PIE_COLORS = [
        (0.9, 0.3, 0.3),  # 红
        (0.3, 0.6, 0.9),  # 蓝
        (0.3, 0.8, 0.4),  # 绿
        (0.9, 0.7, 0.2),  # 黄
        (0.7, 0.3, 0.9),  # 紫
        (0.9, 0.5, 0.2),  # 橙
        (0.4, 0.8, 0.8),  # 青
    ]

    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.name = 'stats'
        self._build_ui()
        Clock.schedule_once(lambda dt: self.refresh(), 0.1)

    def _build_ui(self):
        scroll = MDScrollView()
        root = MDBoxLayout(orientation='vertical', padding='16dp', spacing='16dp',
                           size_hint_y=None)
        root.bind(minimum_height=root.setter('height'))

        # 饼图区域 (MDCard)
        pie_card = MDCard(orientation='vertical', padding='16dp', spacing='8dp', size_hint_y=None, radius=[12, 12, 12, 12], elevation=1)
        pie_card.bind(minimum_height=pie_card.setter('height'))
        pie_card.add_widget(MDLabel(
            text='本月支出分类',
            size_hint_y=None,
            height='40dp',
            font_style='H6'
        ))
        self.pie_chart = PieChart(size_hint_y=None, height='250dp')
        pie_card.add_widget(self.pie_chart)

        self.legend_box = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height='0dp',
            spacing='4dp'
        )
        pie_card.add_widget(self.legend_box)
        root.add_widget(pie_card)

        # 柱状图区域 (MDCard)
        bar_card = MDCard(orientation='vertical', padding='16dp', spacing='8dp', size_hint_y=None, radius=[12, 12, 12, 12], elevation=1)
        bar_card.bind(minimum_height=bar_card.setter('height'))
        bar_card.add_widget(MDLabel(
            text='近6个月收支',
            size_hint_y=None,
            height='40dp',
            font_style='H6'
        ))
        self.bar_chart = BarChart(size_hint_y=None, height='200dp')
        bar_card.add_widget(self.bar_chart)

        legend_bar = MDBoxLayout(orientation='horizontal', size_hint_y=None, height='30dp')
        legend_bar.add_widget(MDLabel(text='■ 收入', theme_text_color='Custom', text_color=(0.2, 0.7, 0.2, 1)))
        legend_bar.add_widget(MDLabel(text='■ 支出', theme_text_color='Custom', text_color=(0.9, 0.2, 0.2, 1)))
        bar_card.add_widget(legend_bar)
        
        root.add_widget(bar_card)

        scroll.add_widget(root)
        self.add_widget(scroll)

    def refresh(self):
        now = datetime.now()

        # 饼图数据
        cat_summary = self.db.get_category_summary(now.year, now.month)
        pie_data = []
        self.legend_box.clear_widgets()
        for i, item in enumerate(cat_summary):
            color = self.PIE_COLORS[i % len(self.PIE_COLORS)]
            pie_data.append((item['name'], item['total'], color))
            # 图例
            label = MDLabel(
                text=f"{'█' * 2} {item['name']}  ¥{item['total']:.2f}",
                theme_text_color='Custom',
                text_color=(*color, 1),
                size_hint_y=None,
                height='24dp'
            )
            self.legend_box.add_widget(label)

        legend_h = len(cat_summary) * 28
        self.legend_box.height = str(legend_h) + 'dp'
        self.pie_chart.set_data(pie_data)

        # 柱状图数据
        monthly = self.db.get_monthly_totals(months=6)
        self.bar_chart.set_data(monthly)
