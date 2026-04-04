from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import MDList, OneLineListItem, TwoLineListItem
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivy.clock import Clock
from datetime import datetime


class SettingsScreen(MDScreen):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.name = 'settings'
        self._dialog = None
        self._build_ui()
        Clock.schedule_once(lambda dt: self.refresh(), 0.1)

    def _build_ui(self):
        scroll = MDScrollView()
        root = MDBoxLayout(
            orientation='vertical',
            padding='8dp',
            spacing='12dp',
            size_hint_y=None,
        )
        root.bind(minimum_height=root.setter('height'))

        # --- 通知监听开关 ---
        root.add_widget(MDLabel(
            text='通知监听',
            font_style='H6',
            size_hint_y=None,
            height='40dp',
        ))
        service_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height='48dp',
        )
        service_row.add_widget(MDLabel(text='自动监听支付宝/微信通知'))
        self.service_switch = MDSwitch(active=False)
        self.service_switch.bind(active=self._on_service_toggle)
        service_row.add_widget(self.service_switch)
        root.add_widget(service_row)

        # --- 手动添加账单 ---
        root.add_widget(MDLabel(
            text='手动添加账单',
            font_style='H6',
            size_hint_y=None,
            height='40dp',
        ))
        add_btn = MDRaisedButton(
            text='+ 添加账单',
            size_hint_y=None,
            height='48dp',
            on_release=lambda x: self._show_add_transaction_dialog(),
        )
        root.add_widget(add_btn)

        # --- 分类管理 ---
        root.add_widget(MDLabel(
            text='分类管理',
            font_style='H6',
            size_hint_y=None,
            height='40dp',
        ))
        add_cat_btn = MDFlatButton(
            text='+ 新增分类',
            size_hint_y=None,
            height='40dp',
            on_release=lambda x: self._show_add_category_dialog(),
        )
        root.add_widget(add_cat_btn)

        self.category_list = MDList(size_hint_y=None)
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
                size_hint_x=0.8,
            ))
            edit_btn = MDIconButton(
                icon='pencil',
                on_release=lambda x, c=cat: self._show_edit_category_dialog(c),
            )
            del_btn = MDIconButton(
                icon='delete',
                theme_icon_color='Custom',
                icon_color=(0.9, 0.2, 0.2, 1),
                on_release=lambda x, cid=cat.id: self._delete_category(cid),
            )
            row.add_widget(edit_btn)
            row.add_widget(del_btn)
            self.category_list.add_widget(row)

    def _on_service_toggle(self, switch, value):
        from src.service.notification_service import start_service, stop_service
        if value:
            start_service()
        else:
            stop_service()

    def _show_add_transaction_dialog(self):
        """手动添加账单对话框"""
        content = MDBoxLayout(
            orientation='vertical',
            spacing='8dp',
            size_hint_y=None,
            height='320dp',
        )
        amount_field = MDTextField(hint_text='金额（元）', input_filter='float')
        merchant_field = MDTextField(hint_text='商家名称')
        note_field = MDTextField(hint_text='备注（可选）')

        # 类型选择（简单用文本字段）
        type_field = MDTextField(hint_text='类型：expense 或 income', text='expense')

        # 分类选择（显示分类名列表，简单用文本字段输入分类名）
        categories = self.db.get_categories()
        cat_names = ', '.join(c.name for c in categories)
        cat_field = MDTextField(hint_text=f'分类（{cat_names}）')

        content.add_widget(amount_field)
        content.add_widget(type_field)
        content.add_widget(merchant_field)
        content.add_widget(cat_field)
        content.add_widget(note_field)

        if self._dialog:
            self._dialog.dismiss()

        self._dialog = MDDialog(
            title='手动添加账单',
            type='custom',
            content_cls=content,
            buttons=[
                MDFlatButton(text='取消', on_release=lambda x: self._dialog.dismiss()),
                MDRaisedButton(
                    text='保存',
                    on_release=lambda x: self._save_manual_transaction(
                        amount_field.text,
                        type_field.text.strip(),
                        merchant_field.text.strip(),
                        cat_field.text.strip(),
                        note_field.text.strip(),
                    )
                ),
            ],
        )
        self._dialog.open()

    def _save_manual_transaction(self, amount_str, type_str, merchant, cat_name, note):
        from src.models.transaction import Transaction
        try:
            amount = float(amount_str)
        except ValueError:
            return  # 金额无效，不保存

        if not merchant:
            return

        # 查找分类 id
        categories = self.db.get_categories()
        cat_id = None
        for c in categories:
            if c.name == cat_name:
                cat_id = c.id
                break
        if cat_id is None:
            # 找"其他"分类
            for c in categories:
                if c.name == '其他':
                    cat_id = c.id
                    break

        t = Transaction(
            id=None,
            amount=amount,
            type=type_str if type_str in ('income', 'expense') else 'expense',
            category_id=cat_id,
            merchant=merchant,
            note=note,
            source='manual',
            created_at=datetime.now().isoformat(timespec='seconds'),
            pending=0,
        )
        self.db.add_transaction(t)
        if self._dialog:
            self._dialog.dismiss()

    def _show_add_category_dialog(self):
        content = MDBoxLayout(orientation='vertical', spacing='8dp', size_hint_y=None, height='160dp')
        name_field = MDTextField(hint_text='分类名称')
        icon_field = MDTextField(hint_text='图标名（如 food-fork-drink）', text='dots-horizontal')
        keywords_field = MDTextField(hint_text='关键词（逗号分隔）')
        content.add_widget(name_field)
        content.add_widget(icon_field)
        content.add_widget(keywords_field)

        if self._dialog:
            self._dialog.dismiss()

        self._dialog = MDDialog(
            title='新增分类',
            type='custom',
            content_cls=content,
            buttons=[
                MDFlatButton(text='取消', on_release=lambda x: self._dialog.dismiss()),
                MDRaisedButton(
                    text='保存',
                    on_release=lambda x: self._save_new_category(
                        name_field.text.strip(),
                        icon_field.text.strip(),
                        keywords_field.text.strip(),
                    )
                ),
            ],
        )
        self._dialog.open()

    def _save_new_category(self, name, icon, keywords):
        from src.models.transaction import Category
        if not name:
            return
        cat = Category(id=None, name=name, icon=icon or 'dots-horizontal', keywords=keywords)
        self.db.add_category(cat)
        if self._dialog:
            self._dialog.dismiss()
        self.refresh()

    def _show_edit_category_dialog(self, cat):
        content = MDBoxLayout(orientation='vertical', spacing='8dp', size_hint_y=None, height='120dp')
        keywords_field = MDTextField(hint_text='关键词（逗号分隔）', text=cat.keywords or '')
        content.add_widget(MDLabel(text=f'编辑分类：{cat.name}', size_hint_y=None, height='40dp'))
        content.add_widget(keywords_field)

        if self._dialog:
            self._dialog.dismiss()

        self._dialog = MDDialog(
            title='编辑关键词',
            type='custom',
            content_cls=content,
            buttons=[
                MDFlatButton(text='取消', on_release=lambda x: self._dialog.dismiss()),
                MDRaisedButton(
                    text='保存',
                    on_release=lambda x: self._save_edit_category(cat, keywords_field.text.strip())
                ),
            ],
        )
        self._dialog.open()

    def _save_edit_category(self, cat, new_keywords):
        from src.models.transaction import Category
        updated = Category(id=cat.id, name=cat.name, icon=cat.icon, keywords=new_keywords)
        self.db.update_category(updated)
        if self._dialog:
            self._dialog.dismiss()
        self.refresh()

    def _delete_category(self, category_id):
        self.db.delete_category(category_id)
        self.refresh()
