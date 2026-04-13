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



class TypeSelector(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = '48dp'
        self.spacing = '10dp'
        self.selected_type = 'expense'
        
        self.btn_expense = MDFlatButton(
            text='支出 (expense)', 
            md_bg_color=(0.9, 0.5, 0.2, 1),
            theme_text_color='Custom', text_color=(1, 1, 1, 1),
            on_release=lambda x: self.select('expense')
        )
        self.btn_income = MDFlatButton(
            text='收入 (income)', 
            md_bg_color=(0.9, 0.9, 0.9, 1),
            theme_text_color='Custom', text_color=(0, 0, 0, 1),
            on_release=lambda x: self.select('income')
        )
        self.add_widget(self.btn_expense)
        self.add_widget(self.btn_income)

    def select(self, t):
        self.selected_type = t
        if t == 'expense':
            self.btn_expense.md_bg_color = (0.9, 0.5, 0.2, 1)
            self.btn_expense.text_color = (1, 1, 1, 1)
            self.btn_income.md_bg_color = (0.9, 0.9, 0.9, 1)
            self.btn_income.text_color = (0, 0, 0, 1)
        else:
            self.btn_income.md_bg_color = (0.2, 0.7, 0.2, 1)
            self.btn_income.text_color = (1, 1, 1, 1)
            self.btn_expense.md_bg_color = (0.9, 0.9, 0.9, 1)
            self.btn_expense.text_color = (0, 0, 0, 1)

class SettingsScreen(MDScreen):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.name = 'settings'
        self._build_ui()
        Clock.schedule_once(lambda dt: self.refresh(), 0.1)
        # 定时刷新权限状态，以便从系统设置返回时能自动更新
        Clock.schedule_interval(lambda dt: self._update_permission_status(), 2.0)

    def _build_ui(self):
        scroll = MDScrollView()
        root = MDBoxLayout(orientation='vertical', padding='8dp', spacing='12dp', size_hint_y=None)
        root.bind(minimum_height=root.setter('height'))

        root.add_widget(MDLabel(text='系统权限管理 (必需)', size_hint_y=None, height='40dp'))

        # 悬浮窗权限行
        overlay_row = MDBoxLayout(orientation='horizontal', size_hint_y=None, height='48dp', spacing='12dp')
        self.overlay_status_label = MDLabel(text="悬浮窗权限：检测中", markup=True, size_hint_x=0.5)
        overlay_row.add_widget(self.overlay_status_label)
        overlay_row.add_widget(MDRaisedButton(
            text='去授权',
            theme_text_color='Custom', text_color=(0, 0, 0, 1),
            on_release=lambda x: self._open_overlay_settings()
        ))
        root.add_widget(overlay_row)

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

        # 悬浮窗服务控制行
        float_row = MDBoxLayout(orientation='horizontal', size_hint_y=None, height='48dp', spacing='12dp')
        float_row.add_widget(MDRaisedButton(
            text='启动悬浮窗',
            theme_text_color='Custom', text_color=(0, 0, 0, 1),
            on_release=lambda x: self._start_float_window()
        ))
        float_row.add_widget(MDRaisedButton(
            text='停止悬浮窗',
            theme_text_color='Custom', text_color=(0, 0, 0, 1),
            on_release=lambda x: self._stop_float_window()
        ))
        root.add_widget(float_row)

        root.add_widget(MDLabel(text='自动记账测试 (模拟系统通知)', size_hint_y=None, height='40dp'))
        
        auto_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height='48dp', spacing='12dp')
        auto_box.add_widget(MDRaisedButton(
            text='模拟支付宝支出',
            theme_text_color='Custom', text_color=(0,0,0,1),
            on_release=lambda x: self._simulate_alipay()
        ))
        auto_box.add_widget(MDRaisedButton(
            text='模拟微信收入',
            theme_text_color='Custom', text_color=(0,0,0,1),
            on_release=lambda x: self._simulate_wechat()
        ))
        root.add_widget(auto_box)

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
        self._update_permission_status()
        self.category_list.clear_widgets()
        for cat in self.db.get_categories():
            row = MDBoxLayout(orientation='horizontal', size_hint_y=None, height='56dp', spacing='4dp')
            row.add_widget(MDLabel(
                text=f"{cat.name}  [{cat.keywords or '无关键词'}]",
                size_hint_x=0.7,
            ))
            row.add_widget(MDFlatButton(
                text='编辑',
                theme_text_color='Custom',
                text_color=(0.9, 0.5, 0.2, 1), # 橙色
                on_release=lambda x, c=cat: self._show_edit_category_popup(c),
            ))
            row.add_widget(MDFlatButton(
                text='删除',
                theme_text_color='Custom',
                text_color=(0.9, 0.3, 0.3, 1), # 红色
                on_release=lambda x, cid=cat.id: self._delete_category(cid),
            ))
            self.category_list.add_widget(row)



    def _check_notification_permission(self):
        from kivy.utils import platform
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                context = PythonActivity.mActivity.getApplicationContext()
                
                # 方法1: 使用 Android 8.1+ (API 27+) 的官方接口检查
                try:
                    ComponentName = autoclass('android.content.ComponentName')
                    NotificationManager = autoclass('android.app.NotificationManager')
                    Context = autoclass('android.content.Context')
                    nm = context.getSystemService(Context.NOTIFICATION_SERVICE)
                    cn = ComponentName(context, "org.example.autobookkeeping.NLService")
                    if nm.isNotificationListenerAccessGranted(cn):
                        return True
                except Exception:
                    pass
                
                # 方法2: 降级读取 Secure Settings
                Settings = autoclass('android.provider.Settings')
                enabled_listeners = Settings.Secure.getString(context.getContentResolver(), "enabled_notification_listeners")
                package_name = context.getPackageName()
                
                if enabled_listeners and package_name in enabled_listeners:
                    return True
                    
                return False
            except Exception as e:
                return False
        return True

    def _check_accessibility_permission(self):
        from kivy.utils import platform
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                context = PythonActivity.mActivity.getApplicationContext()

                # Primary: AccessibilityManager.getEnabledAccessibilityServiceList()
                try:
                    AccessibilityManager = autoclass('android.view.accessibility.AccessibilityManager')
                    AccessibilityServiceInfo = autoclass('android.accessibilityservice.AccessibilityServiceInfo')
                    Context = autoclass('android.content.Context')
                    am = context.getSystemService(Context.ACCESSIBILITY_SERVICE)
                    enabled_services = am.getEnabledAccessibilityServiceList(
                        AccessibilityServiceInfo.FEEDBACK_ALL_MASK
                    )
                    for i in range(enabled_services.size()):
                        svc = enabled_services.get(i)
                        if 'autobookkeeping' in svc.getId().lower():
                            return True
                    return False
                except Exception:
                    pass

                # Fallback: Settings.Secure
                Settings = autoclass('android.provider.Settings')
                enabled = Settings.Secure.getString(
                    context.getContentResolver(),
                    "enabled_accessibility_services"
                )
                return bool(enabled and 'autobookkeeping' in enabled.lower())
            except Exception:
                return False
        return True

    def _rebind_service(self):
        from kivy.utils import platform
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                context = PythonActivity.mActivity.getApplicationContext()
                ComponentName = autoclass('android.content.ComponentName')
                PackageManager = autoclass('android.content.pm.PackageManager')
                cn = ComponentName(context, "org.example.autobookkeeping.NLService")
                pm = context.getPackageManager()
                pm.setComponentEnabledSetting(cn, PackageManager.COMPONENT_ENABLED_STATE_DISABLED, PackageManager.DONT_KILL_APP)
                pm.setComponentEnabledSetting(cn, PackageManager.COMPONENT_ENABLED_STATE_ENABLED, PackageManager.DONT_KILL_APP)
                self._show_toast("已尝试重启服务，请重新测试")
            except Exception as e:
                self._show_toast("重启失败: " + str(e))
        else:
            self._show_toast("仅在 Android 设备上可用")

    def _open_notification_settings(self):
        from kivy.utils import platform
        if platform == 'android':
            try:
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                Settings = autoclass('android.provider.Settings')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                
                # 提示用户如果受限怎么办
                self._show_toast("如遇“受限制的设置”，请在应用信息的右上角解除限制")
                
                try:
                    # 尝试打开标准通知监听设置
                    intent = Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)
                    PythonActivity.mActivity.startActivity(intent)
                except Exception as e:
                    # 兼容部分魔改系统（如荣耀/华为）
                    try:
                        Uri = autoclass('android.net.Uri')
                        intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS)
                        uri = Uri.fromParts("package", PythonActivity.mActivity.getPackageName(), None)
                        intent.setData(uri)
                        PythonActivity.mActivity.startActivity(intent)
                        self._show_toast("请在权限管理中手动寻找并开启'通知读取/使用权'")
                    except Exception as e2:
                        self._show_toast("无法打开设置，请在系统设置中搜索'通知使用权'")
            except Exception as e:
                self._show_toast("执行出错: " + str(e))
        else:
            self._show_toast("仅在 Android 设备上可用")

    def _open_accessibility_settings(self):
        from kivy.utils import platform
        if platform == 'android':
            try:
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                Settings = autoclass('android.provider.Settings')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                
                try:
                    intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
                    PythonActivity.mActivity.startActivity(intent)
                    self._show_toast("请在无障碍设置中找到“自动记账”并开启")
                except Exception as e:
                    self._show_toast("无法打开设置，请在系统设置中搜索“无障碍”或“辅助功能”")
            except Exception as e:
                self._show_toast("执行出错: " + str(e))
        else:
            self._show_toast("仅在 Android 设备上可用")

    def _check_overlay_permission(self):
        from kivy.utils import platform
        if platform == 'android':
            try:
                from jnius import autoclass
                Settings = autoclass('android.provider.Settings')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                context = PythonActivity.mActivity.getApplicationContext()
                return Settings.canDrawOverlays(context)
            except Exception:
                return False
        return True

    def _open_overlay_settings(self):
        from kivy.utils import platform
        if platform == 'android':
            try:
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                Settings = autoclass('android.provider.Settings')
                Uri = autoclass('android.net.Uri')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION)
                uri = Uri.fromParts("package", PythonActivity.mActivity.getPackageName(), None)
                intent.setData(uri)
                PythonActivity.mActivity.startActivity(intent)
            except Exception as e:
                self._show_toast("无法打开设置: " + str(e))
        else:
            self._show_toast("仅在 Android 设备上可用")

    def _start_float_window(self):
        from kivy.utils import platform
        if platform == 'android':
            if not self._check_overlay_permission():
                self._open_overlay_settings()
                return
            try:
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                intent = Intent()
                intent.setClassName('org.example.autobookkeeping',
                                    'org.example.autobookkeeping.FloatWindowService')
                PythonActivity.mActivity.startService(intent)
                self._show_toast("悬浮窗已启动")
            except Exception as e:
                self._show_toast("启动失败: " + str(e))
        else:
            self._show_toast("仅在 Android 设备上可用")

    def _stop_float_window(self):
        from kivy.utils import platform
        if platform == 'android':
            try:
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                intent = Intent()
                intent.setClassName('org.example.autobookkeeping',
                                    'org.example.autobookkeeping.FloatWindowService')
                PythonActivity.mActivity.stopService(intent)
                self._show_toast("悬浮窗已停止")
            except Exception as e:
                self._show_toast("停止失败: " + str(e))
        else:
            self._show_toast("仅在 Android 设备上可用")

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
        has_overlay = self._check_overlay_permission()
        self.overlay_status_label.text = (
            "悬浮窗权限：[color=00CC00]已授权[/color]" if has_overlay
            else "悬浮窗权限：[color=FF3333]未授权[/color]"
        )

    def _simulate_alipay(self):
        from src.service.notification_service import NotificationHandler
        handler = NotificationHandler(self.db.db_path)
        success = handler.handle('com.eg.android.AlipayGphone', '支付宝消息支出 25.50元 商家：麦当劳')
        self._show_toast("已模拟识别并记录一条支付宝支出：25.50元 (麦当劳)")
        
    def _simulate_wechat(self):
        from src.service.notification_service import NotificationHandler
        handler = NotificationHandler(self.db.db_path)
        success = handler.handle('com.tencent.mm', '你已收到100.00元转账')
        self._show_toast("已模拟识别并记录一条微信收入：100.00元 (转账)")
        
    def _show_toast(self, text):
        from kivy.uix.label import Label
        from kivy.uix.popup import Popup
        popup = Popup(title='模拟通知已识别', content=Label(text=text, font_name='NotoSansSC-Regular.ttf'), size_hint=(0.8, 0.3), auto_dismiss=True)
        popup.open()
        
    def _show_add_transaction_popup(self):
        content = BoxLayout(orientation='vertical', spacing='12dp', padding='12dp')
        
        # 白底背景
        from kivy.graphics import Color, Rectangle
        with content.canvas.before:
            Color(1, 1, 1, 1)
            self._content_rect = Rectangle(size=content.size, pos=content.pos)
        def update_rect(instance, value):
            self._content_rect.pos = instance.pos
            self._content_rect.size = instance.size
        content.bind(pos=update_rect, size=update_rect)

        amount_field = MDTextField(hint_text='金额（元）', input_filter='float', text_color_normal=(0,0,0,1))
        
        type_selector = TypeSelector()
        
        merchant_field = MDTextField(hint_text='商家名称', text_color_normal=(0,0,0,1))
        categories = self.db.get_categories()
        cat_field = MDTextField(hint_text=f'分类（{", ".join(c.name for c in categories)}）', text_color_normal=(0,0,0,1))
        note_field = MDTextField(hint_text='备注（可选）', text_color_normal=(0,0,0,1))
        
        content.add_widget(amount_field)
        content.add_widget(type_selector)
        content.add_widget(merchant_field)
        content.add_widget(cat_field)
        content.add_widget(note_field)

        popup = Popup(
            title='手动添加账单', 
            content=content, 
            size_hint=(0.9, 0.85),
            background='',
            background_color=(0.95, 0.95, 0.95, 1),
            title_color=(0, 0, 0, 1),
            separator_color=(0.9, 0.5, 0.2, 1)
        )
        
        btn_row = BoxLayout(size_hint_y=None, height='48dp', spacing='8dp')
        btn_row.add_widget(MDFlatButton(text='取消', on_release=lambda x: popup.dismiss(), theme_text_color='Custom', text_color=(0,0,0,1)))
        btn_row.add_widget(MDRaisedButton(
            text='保存',
            on_release=lambda x: self._save_transaction(
                amount_field.text, type_selector.selected_type,
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

        
        # 白底背景
        from kivy.graphics import Color, Rectangle
        if not hasattr(self, '_content_rect_dict'):
            self._content_rect_dict = {}
        with content.canvas.before:
            Color(1, 1, 1, 1)
            rect = Rectangle(size=content.size, pos=content.pos)
            self._content_rect_dict[id(content)] = rect
        def update_rect__show_add_category_popup(instance, value):
            self._content_rect_dict[id(instance)].pos = instance.pos
            self._content_rect_dict[id(instance)].size = instance.size
        content.bind(pos=update_rect__show_add_category_popup, size=update_rect__show_add_category_popup)

        popup = Popup(title='新增分类', content=content, size_hint=(0.9, 0.6), background='', background_color=(0.95, 0.95, 0.95, 1), title_color=(0, 0, 0, 1), separator_color=(0.9, 0.5, 0.2, 1))
        btn_row = BoxLayout(size_hint_y=None, height='48dp', spacing='8dp')
        btn_row.add_widget(MDFlatButton(text='取消', on_release=lambda x: popup.dismiss(), theme_text_color='Custom', text_color=(0,0,0,1)))
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
        self._notify_categories_changed()

    def _save_edit_category(self, cat, new_keywords, popup):
        from src.models.transaction import Category
        self.db.update_category(Category(id=cat.id, name=cat.name, icon=cat.icon, keywords=new_keywords))
        popup.dismiss()
        self.refresh()
        self._notify_categories_changed()

    def _delete_category(self, category_id):
        self.db.delete_category(category_id)
        self.refresh()
        self._notify_categories_changed()

    def _notify_categories_changed(self):
        try:
            from kivy.app import App
            app = App.get_running_app()
            if hasattr(app, '_send_categories_broadcast'):
                app._send_categories_broadcast()
        except Exception:
            pass
        content = BoxLayout(orientation='vertical', spacing='8dp', padding='8dp')
        content.add_widget(MDLabel(text=f'编辑：{cat.name}', size_hint_y=None, height='40dp'))
        keywords_field = MDTextField(hint_text='关键词（逗号分隔）', text=cat.keywords or '')
        content.add_widget(keywords_field)

        
        # 白底背景
        from kivy.graphics import Color, Rectangle
        if not hasattr(self, '_content_rect_dict'):
            self._content_rect_dict = {}
        with content.canvas.before:
            Color(1, 1, 1, 1)
            rect = Rectangle(size=content.size, pos=content.pos)
            self._content_rect_dict[id(content)] = rect
        def update_rect__show_edit_category_popup(instance, value):
            self._content_rect_dict[id(instance)].pos = instance.pos
            self._content_rect_dict[id(instance)].size = instance.size
        content.bind(pos=update_rect__show_edit_category_popup, size=update_rect__show_edit_category_popup)

        popup = Popup(title='编辑关键词', content=content, size_hint=(0.9, 0.5), background='', background_color=(0.95, 0.95, 0.95, 1), title_color=(0, 0, 0, 1), separator_color=(0.9, 0.5, 0.2, 1))
        btn_row = BoxLayout(size_hint_y=None, height='48dp', spacing='8dp')
        btn_row.add_widget(MDFlatButton(text='取消', on_release=lambda x: popup.dismiss(), theme_text_color='Custom', text_color=(0,0,0,1)))
        btn_row.add_widget(MDRaisedButton(
            text='保存',
            on_release=lambda x: self._save_edit_category(cat, keywords_field.text.strip(), popup)
        ))
        content.add_widget(btn_row)
        popup.open()


