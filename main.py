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
                for font_name in ['Roboto', 'RobotoMedium', 'Icons']:
                    try:
                        LabelBase.register(name=font_name, fn_regular=fp,
                            fn_bold=fp, fn_italic=fp, fn_bolditalic=fp)
                    except Exception:
                        pass
                break


    class BookkeepingApp(MDApp):
        def build(self):
            self.theme_cls.primary_palette = "Blue"
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
                height='56dp',
                md_bg_color=self.theme_cls.primary_color,
            )
            self.btn_home = MDFlatButton(
                text='首页', size_hint_x=0.33,
                theme_text_color='Custom', text_color=(1, 1, 1, 1),
                on_release=lambda x: self._switch('home'),
            )
            self.btn_stats = MDFlatButton(
                text='统计', size_hint_x=0.33,
                theme_text_color='Custom', text_color=(1, 1, 1, 1),
                on_release=lambda x: self._switch('stats'),
            )
            self.btn_settings = MDFlatButton(
                text='设置', size_hint_x=0.34,
                theme_text_color='Custom', text_color=(1, 1, 1, 1),
                on_release=lambda x: self._switch('settings'),
            )
            nav_bar.add_widget(self.btn_home)
            nav_bar.add_widget(self.btn_stats)
            nav_bar.add_widget(self.btn_settings)

            root.add_widget(self.sm)
            root.add_widget(nav_bar)
            return root

        def _switch(self, name):
            self.sm.current = name
            if name == 'home':
                self.home_screen.refresh()
            elif name == 'stats':
                self.stats_screen.refresh()


    if __name__ == '__main__':
        BookkeepingApp().run()

except Exception:
    traceback.print_exc()
