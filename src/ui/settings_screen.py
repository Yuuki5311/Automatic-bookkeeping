from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from datetime import datetime


class SettingsScreen(MDScreen):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.name = 'settings'
        self._build_ui()
        Clock.schedule_once(lambda dt: self.refresh(), 0.1)

    def _build_ui(self):
        scroll = MDScrollView()
        root = MDBoxLayout(orientation='vertical', padding='8dp', spacing='12dp', size_hint_y=None)
        root.bind(minimum_height=root.setter('height'))

        root.add_widget(MDLabel(text='手动添加账单', size_hint_y=None, height='40dp'))
        root.add_widget(MDRaisedButton(
            text='+ 添加账单', size_hint_y=None, height='48dp',
            on_release=lambda x: self._show_add_transaction_popup(),
        ))

        root.add_widget(MDLabel(text='分类管理', size_hint_y=None, height='40dp'))
        root.add_widget(MDFlatButton(
            text='+ 新增分类', size_hint_y=None, height='40dp',
            on_release=lambda x: self._show_add_category_popup(),
        ))

        self.category_list = MDBoxLayout(orientation='vertical', size_hint_y=None, spacing='4dp')
        self.category_list.bind(minimum_height=self.category_list.setter('height'))
        root.add_widget(self.category_list)

        scroll.add_widget(root)
        self.add_widget(scroll)

    def refresh(self):
        self.category_list.clear_widgets()
        for cat in self.db.get_categories():
            row = MDBoxLayout(orientation='horizontal', size_hint_y=None, height='56dp')
            row.add_widget(MDLabel(
                text=f"{cat.name}  [{cat.keywords or '无关键词'}]",
                size_hint_x=0.7,
            ))
            row.add_widget(MDIconButton(
                icon='pencil',
                on_release=lambda x, c=cat: self._show_edit_category_popup(c),
            ))
            row.add_widget(MDIconButton(
                icon='delete',
                on_release=lambda x, cid=cat.id: self._delete_category(cid),
            ))
            self.category_list.add_widget(row)

    def _show_add_transaction_popup(self):
        content = BoxLayout(orientation='vertical', spacing='8dp', padding='8dp')
        amount_field = MDTextField(hint_text='金额（元）', input_filter='float')
        type_field = MDTextField(hint_text='expense 或 income', text='expense')
        merchant_field = MDTextField(hint_text='商家名称')
        categories = self.db.get_categories()
        cat_field = MDTextField(hint_text=f'分类（{", ".join(c.name for c in categories)}）')
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

    def _show_add_category_popup(self):
        content = BoxLayout(orientation='vertical', spacing='8dp', padding='8dp')
        name_field = MDTextField(hint_text='分类名称')
        icon_field = MDTextField(hint_text='图标名', text='dots-horizontal')
        keywords_field = MDTextField(hint_text='关键词（逗号分隔）')
        for w in [name_field, icon_field, keywords_field]:
            content.add_widget(w)

        popup = Popup(title='新增分类', content=content, size_hint=(0.9, 0.6))
        btn_row = BoxLayout(size_hint_y=None, height='48dp', spacing='8dp')
        btn_row.add_widget(MDFlatButton(text='取消', on_release=lambda x: popup.dismiss()))
        btn_row.add_widget(MDRaisedButton(
            text='保存',
            on_release=lambda x: self._save_category(
                name_field.text.strip(), icon_field.text.strip(),
                keywords_field.text.strip(), popup,
            )
        ))
        content.add_widget(btn_row)
        popup.open()

    def _save_category(self, name, icon, keywords, popup):
        from src.models.transaction import Category
        if not name:
            return
        self.db.add_category(Category(id=None, name=name, icon=icon or 'dots-horizontal', keywords=keywords))
        popup.dismiss()
        self.refresh()

    def _show_edit_category_popup(self, cat):
        content = BoxLayout(orientation='vertical', spacing='8dp', padding='8dp')
        content.add_widget(MDLabel(text=f'编辑：{cat.name}', size_hint_y=None, height='40dp'))
        keywords_field = MDTextField(hint_text='关键词（逗号分隔）', text=cat.keywords or '')
        content.add_widget(keywords_field)

        popup = Popup(title='编辑关键词', content=content, size_hint=(0.9, 0.5))
        btn_row = BoxLayout(size_hint_y=None, height='48dp', spacing='8dp')
        btn_row.add_widget(MDFlatButton(text='取消', on_release=lambda x: popup.dismiss()))
        btn_row.add_widget(MDRaisedButton(
            text='保存',
            on_release=lambda x: self._save_edit_category(cat, keywords_field.text.strip(), popup)
        ))
        content.add_widget(btn_row)
        popup.open()

    def _save_edit_category(self, cat, new_keywords, popup):
        from src.models.transaction import Category
        self.db.update_category(Category(id=cat.id, name=cat.name, icon=cat.icon, keywords=new_keywords))
        popup.dismiss()
        self.refresh()

    def _delete_category(self, category_id):
        self.db.delete_category(category_id)
        self.refresh()
