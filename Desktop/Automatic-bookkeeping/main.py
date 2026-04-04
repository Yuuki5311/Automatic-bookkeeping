"""
自动记账 App 入口
"""
from kivymd.app import MDApp
from kivymd.uix.navigationbar import MDNavigationBar, MDNavigationItem
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.core.window import Window

from src.core.database import Database
from src.ui.home_screen import HomeScreen
from src.ui.stats_screen import StatsScreen
from src.ui.settings_screen import SettingsScreen


class BookkeepingApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"

        # 初始化数据库
        self.db = Database("bookkeeping.db")
        self.db.init_db()

        # 根布局：屏幕管理器 + 底部导航栏
        root = MDBoxLayout(orientation='vertical')

        self.screen_manager = MDScreenManager()
        self.screen_manager.add_widget(HomeScreen(db=self.db))
        self.screen_manager.add_widget(StatsScreen(db=self.db))
        self.screen_manager.add_widget(SettingsScreen(db=self.db))

        nav_bar = MDNavigationBar(on_switch_tabs=self._on_tab_switch)
        nav_bar.add_widget(MDNavigationItem(
            icon='home',
            text='首页',
            name='home',
        ))
        nav_bar.add_widget(MDNavigationItem(
            icon='chart-pie',
            text='统计',
            name='stats',
        ))
        nav_bar.add_widget(MDNavigationItem(
            icon='cog',
            text='设置',
            name='settings',
        ))

        root.add_widget(self.screen_manager)
        root.add_widget(nav_bar)

        return root

    def _on_tab_switch(self, instance_navigation_bar, instance_navigation_item, item_icon, item_name):
        self.screen_manager.current = item_name
        # 切换到统计页时刷新数据
        if item_name == 'stats':
            self.screen_manager.get_screen('stats').refresh()
        elif item_name == 'home':
            self.screen_manager.get_screen('home').refresh()


if __name__ == '__main__':
    BookkeepingApp().run()
