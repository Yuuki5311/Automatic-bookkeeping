"""
自动记账 App 入口
"""
import sys
import traceback
import os


def _setup_crash_log():
    base = '/data/data/org.example.autobookkeeping/files'
    log_path = os.path.join(base, 'crash.txt')
    try:
        os.makedirs(base, exist_ok=True)
        f = open(log_path, 'w', buffering=1)
        sys.stderr = f
        sys.stdout = f
    except Exception:
        pass


_setup_crash_log()

try:
    from kivy.core.text import LabelBase
    from kivy.resources import resource_add_path
    from kivymd.app import MDApp
    from kivymd.uix.boxlayout import MDBoxLayout
    from kivymd.uix.button import MDFlatButton, MDRaisedButton
    from kivymd.uix.screenmanager import MDScreenManager
    from kivymd.uix.label import MDLabel
    from kivymd.icon_definitions import md_icons

    from src.core.database import Database
    from src.ui.home_screen import HomeScreen
    from src.ui.stats_screen import StatsScreen
    from src.ui.settings_screen import SettingsScreen


    def _register_chinese_font():
        for candidate in [
            '/data/data/org.example.autobookkeeping/files/app',
            os.path.dirname(os.path.abspath(__file__)),
            '.',
        ]:
            fp = os.path.join(candidate, 'NotoSansSC-Regular.ttf')
            if os.path.exists(fp):
                resource_add_path(candidate)
                for font_name in ['Roboto', 'RobotoMedium']:
                    try:
                        LabelBase.register(name=font_name, fn_regular=fp,
                            fn_bold=fp, fn_italic=fp, fn_bolditalic=fp)
                    except Exception:
                        pass
                break


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
                ('home', 'home', '首页'),
                ('stats', 'chart-bar', '统计'),
                ('settings', 'cog', '设置'),
            ]
            for name, icon, label in nav_items:
                btn_box = MDBoxLayout(
                    orientation='vertical',
                    size_hint_x=0.33,
                    padding='4dp',
                )
                icon_lbl = MDLabel(
                    text=md_icons[icon],
                    font_style='Icon',
                    halign='center',
                    size_hint_y=None,
                    height='28dp',
                    theme_text_color='Custom',
                    text_color=(1, 1, 1, 1),
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

        def on_start(self):
            from src.service.notification_service import start_service
            start_service()

        def _nav_touch(self, instance, touch, name):
            if instance.collide_point(*touch.pos):
                self._switch(name)

        def _update_nav_highlight(self, active_name):
            for name, (box, icon_lbl, text_lbl) in self._nav_btns.items():
                if name == active_name:
                    box.md_bg_color = (1, 1, 1, 0.25)
                    text_lbl.text_color = (1, 1, 1, 1)
                    icon_lbl.text_color = (1, 1, 1, 1)
                else:
                    box.md_bg_color = (0, 0, 0, 0)
                    text_lbl.text_color = (1, 1, 1, 0.7)
                    icon_lbl.text_color = (1, 1, 1, 0.7)

        def _switch(self, name):
            self.sm.current = name
            self._update_nav_highlight(name)
            if name == 'home':
                self.home_screen.refresh()
            elif name == 'stats':
                self.stats_screen.refresh()
            elif name == 'settings':
                self.settings_screen.refresh()


    if __name__ == '__main__':
        BookkeepingApp().run()

except Exception:
    traceback.print_exc()
