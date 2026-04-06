from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from datetime import datetime


class HomeScreen(MDScreen):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.name = 'home'
        self._build_ui()
        Clock.schedule_once(lambda dt: self.refresh(), 0.1)

    def _build_ui(self):
        root = MDBoxLayout(orientation='vertical', padding='8dp', spacing='8dp')

        summary_card = MDCard(
            orientation='horizontal',
            size_hint_y=None,
            height='100dp',
            padding='16dp',
            radius=[12, 12, 12, 12],
            elevation=0,
        )
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

        scroll = MDScrollView()
        self.transaction_list = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing='8dp',
            padding=[8, 8, 8, 8],
        )
        self.transaction_list.bind(minimum_height=self.transaction_list.setter('height'))
        scroll.add_widget(self.transaction_list)
        root.add_widget(scroll)

        self.add_widget(root)

    def refresh(self):
        now = datetime.now()
        summary = self.db.get_monthly_summary(now.year, now.month)
        self.income_label.text = '本月收入'
        self.income_amount.text = f"¥{summary['income']:.2f}"
        self.expense_label.text = '本月支出'
        self.expense_amount.text = f"¥{summary['expense']:.2f}"

        self.transaction_list.clear_widgets()
        categories = {c.id: c for c in self.db.get_categories()}
        transactions = self.db.get_transactions(limit=50)

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
            lbl = MDLabel(
                text=amount_str,
                theme_text_color='Custom',
                text_color=amount_color,
                halign='right',
                size_hint_y=0.55,
                font_style='Subtitle2',
            )
            lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
            right.add_widget(lbl)
            date_lbl = MDLabel(
                text=time_str,
                theme_text_color='Custom',
                text_color=(0.6, 0.6, 0.6, 1),
                halign='right',
                size_hint_y=0.45,
                font_style='Caption',
            )
            date_lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
            right.add_widget(date_lbl)

            card.add_widget(left)
            card.add_widget(right)

            tid = t.id
            card.bind(on_touch_down=lambda inst, touch, _id=tid:
                self._on_row_touch(inst, touch, _id))
            self.transaction_list.add_widget(card)

    def _on_row_touch(self, instance, touch, transaction_id):
        if instance.collide_point(*touch.pos):
            self.show_transaction_detail(transaction_id)

    def show_transaction_detail(self, transaction_id):
        t = self.db.get_transaction(transaction_id)
        if not t:
            return
        categories = {c.id: c.name for c in self.db.get_categories()}
        cat_name = categories.get(t.category_id, '未分类')

        content = BoxLayout(orientation='vertical', spacing='8dp', padding='8dp')
        content.add_widget(MDLabel(text=f"商家：{t.merchant}"))
        content.add_widget(MDLabel(text=f"金额：¥{t.amount:.2f}"))
        content.add_widget(MDLabel(text=f"类型：{'支出' if t.type == 'expense' else '收入'}"))
        content.add_widget(MDLabel(text=f"分类：{cat_name}"))
        content.add_widget(MDLabel(text=f"时间：{t.created_at}"))
        if t.note:
            content.add_widget(MDLabel(text=f"备注：{t.note}"))

        popup = Popup(title='账单详情', content=content, size_hint=(0.9, 0.7))
        btn_row = BoxLayout(size_hint_y=None, height='48dp', spacing='8dp')
        btn_row.add_widget(MDFlatButton(
            text='删除',
            on_release=lambda x: self._delete_transaction(transaction_id, popup),
        ))
        btn_row.add_widget(MDFlatButton(text='关闭', on_release=lambda x: popup.dismiss()))
        content.add_widget(btn_row)
        popup.open()

    def _delete_transaction(self, transaction_id, popup):
        self.db.delete_transaction(transaction_id)
        popup.dismiss()
        self.refresh()
