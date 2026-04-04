"""
Android 通知监听服务。

在 Android 上运行时：通过 pyjnius 调用 NotificationListenerService。
在桌面环境运行时：提供模拟接口用于测试。
"""

import os
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# 检测是否在 Android 环境
ANDROID = os.environ.get('ANDROID_ARGUMENT') is not None or os.path.exists('/system/build.prop')

if ANDROID:
    try:
        from jnius import autoclass, PythonJavaClass, java_method
        Service = autoclass('android.app.Service')
        NotificationListenerService = autoclass('android.service.notification.NotificationListenerService')
        StatusBarNotification = autoclass('android.service.notification.StatusBarNotification')
        PythonService = autoclass('org.kivy.android.PythonService')
    except Exception as e:
        logger.warning(f"pyjnius import failed: {e}")
        ANDROID = False


class NotificationHandler:
    """
    处理收到的通知，解析并存入数据库。
    可在桌面环境独立测试。
    """

    def __init__(self, db_path: str = "bookkeeping.db"):
        from src.core.database import Database
        from src.core.parser import parse_notification
        from src.core.categorizer import categorize
        self.db = Database(db_path)
        self.db.init_db()
        self._parse = parse_notification
        self._categorize = categorize

    def handle(self, package_name: str, text: str, posted_at: Optional[str] = None) -> bool:
        """
        处理一条通知。
        返回 True 表示成功解析并存储，False 表示无法解析（已记入 pending）。
        """
        from src.models.transaction import Transaction

        timestamp = posted_at or datetime.now().isoformat(timespec='seconds')
        result = self._parse(package_name, text)

        if result is None:
            # 无法解析，记入 pending 队列
            t = Transaction(
                id=None,
                amount=0.0,
                type='expense',
                category_id=None,
                merchant='未知',
                note=text[:200],  # 保存原始文本供用户查看
                source=package_name,
                created_at=timestamp,
                pending=1
            )
            self.db.add_transaction(t)
            logger.info(f"Unrecognized notification saved as pending: {text[:50]}")
            return False

        # 自动分类
        categories = self.db.get_categories()
        category_id = self._categorize(result.merchant, categories)

        t = Transaction(
            id=None,
            amount=result.amount,
            type=result.type,
            category_id=category_id,
            merchant=result.merchant,
            note='',
            source=result.source,
            created_at=timestamp,
            pending=0
        )
        self.db.add_transaction(t)
        logger.info(f"Transaction saved: {result.type} {result.amount} from {result.merchant}")
        return True


def start_service():
    """启动通知监听服务（Android 环境）。"""
    if not ANDROID:
        logger.warning("start_service() called in non-Android environment, skipping.")
        return

    try:
        service = PythonService.mService
        # 通知监听服务需要用户在系统设置中手动授权
        # 这里只记录日志，实际监听由 Android 系统回调触发
        logger.info("Notification listener service started.")
    except Exception as e:
        logger.error(f"Failed to start service: {e}")


def stop_service():
    """停止通知监听服务（Android 环境）。"""
    if not ANDROID:
        return
    try:
        logger.info("Notification listener service stopped.")
    except Exception as e:
        logger.error(f"Failed to stop service: {e}")
