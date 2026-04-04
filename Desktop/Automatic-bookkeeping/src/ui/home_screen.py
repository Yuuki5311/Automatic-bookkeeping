from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.list import MDList, TwoLineAvatarIconListItem, IconLeftWidget
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivy.properties import StringProperty, ObjectProperty
from kivy.clock import Clock
from datetime import datetime


class TransactionItem(TwoLineAvatarIconListItem):
    """单条账单列表项"""
    transaction_id = None

    def on_release(self):
        # 触发父屏幕的 show_detail 方法
        screen = self.parent
        while screen and not hasattr(screen, 'show_transaction_detail'):
            screen = screen.parent
        if screen:
            screen.show_transaction_detail(self.transaction_id)


class HomeScreen(MDScreen):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.name = 'home'
        self._dialog = None
        self._build_ui()
        Clock.schedule_once(lambda dt: self.refresh(), 0.1)

    def _build_ui(self):
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.scrollview import MDScrollView

        root = MDBoxLayout(orientation='vertical', padding='8dp', spacing='8dp')

        # 汇总卡片
        self.summary_card = MDCard(
            orientation='vertical',
            padding='16dp',
            size_hint_y=None,
            height='100dp',
            elevation=2,
        )
        self.income_label = MDLabel(text='本月收入：¥0.00', theme_text_color='Custom', text_color=(0.2, 0.7, 0.2, 1))
        self.expense_label = MDLabel(text='本月支出：¥0.00', theme_text_color='Custom', text_color=(0.9, 0.2, 0.2, 1))
        self.summary_card.add_widget(self.income_label)
        self.summary_card.add_widget(self.expense_label)
        root.add_widget(self.summary_card)

        # 账单列表
        scroll = MDScrollView()
        self.transaction_list = MDList()
        scroll.add_widget(self.transaction_list)
        root.add_widget(scroll)

        self.add_widget(root)

    def refresh(self):
        """刷新数据"""
        now = datetime.now()
        summary = self.db.get_monthly_summary(now.year, now.month)
        self.income_label.text = f"本月收入：¥{summary['income']:.2f}"
        self.expense_label.text = f"本月支出：¥{summary['expense']:.2f}"

        self.transaction_list.clear_widgets()
        categories = {c.id: c for c in self.db.get_categories()}
        transactions = self.db.get_transactions(limit=50)

        for t in transactions:
            cat = categories.get(t.category_id)
            cat_name = cat.name if cat else '未分类'
            icon_name = cat.icon if cat else 'help-circle'

            amount_str = f"{'−' if t.type == 'expense' else '+'} ¥{t.amount:.2f}"
            time_str = t.created_at[:10] if t.created_at else ''

            item = TransactionItem(
                text=f"{t.merchant}  {amount_str}",
                secondary_text=f"{cat_name}  {time_str}",
            )
            item.transaction_id = t.id

            icon = IconLeftWidget(icon=icon_name)
            item.add_widget(icon)

            # 待分类高亮
            if t.pending == 1:
                item.bg_color = (1, 0.6, 0.1, 0.15)

            self.transaction_list.add_widget(item)

    def show_transaction_detail(self, transaction_id):
        """显示账单详情对话框"""
        t = self.db.get_transaction(transaction_id)
        if not t:
            return

        categories = {c.id: c.name for c in self.db.get_categories()}
        cat_name = categories.get(t.category_id, '未分类')

        content = MDBoxLayout(orientation='vertical', spacing='8dp', size_hint_y=None, height='200dp')
        content.add_widget(MDLabel(text=f"商家：{t.merchant}"))
        content.add_widget(MDLabel(text=f"金额：¥{t.amount:.2f}"))
        content.add_widget(MDLabel(text=f"类型：{'支出' if t.type == 'expense' else '收入'}"))
        content.add_widget(MDLabel(text=f"分类：{cat_name}"))
        content.add_widget(MDLabel(text=f"来源：{t.source}"))
        content.add_widget(MDLabel(text=f"时间：{t.created_at}"))
        if t.note:
            content.add_widget(MDLabel(text=f"备注：{t.note}"))

        if self._dialog:
            self._dialog.dismiss()

        self._dialog = MDDialog(
            title='账单详情',
            type='custom',
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text='删除',
                    theme_text_color='Custom',
                    text_color=(0.9, 0.2, 0.2, 1),
                    on_release=lambda x: self._delete_transaction(transaction_id)
                ),
                MDFlatButton(text='关闭', on_release=lambda x: self._dialog.dismiss()),
            ],
        )
        self._dialog.open()

    def _delete_transaction(self, transaction_id):
        self.db.delete_transaction(transaction_id)
        if self._dialog:
            self._dialog.dismiss()
        self.refresh()
