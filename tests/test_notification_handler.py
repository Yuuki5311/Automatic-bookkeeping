import pytest
from unittest.mock import patch
from src.service.notification_service import NotificationHandler

@pytest.fixture
def handler(tmp_path):
    h = NotificationHandler(db_path=str(tmp_path / "test.db"))
    return h

def test_handle_alipay_expense(handler):
    # 支付宝支出通知 → 成功解析，返回 True，数据库有记录
    result = handler.handle(
        'com.eg.android.AlipayGphone',
        '支付宝消息支出 25.50元 商家：麦当劳'
    )
    assert result is True
    txns = handler.db.get_transactions()
    assert len(txns) == 1
    assert txns[0].amount == 25.50
    assert txns[0].merchant == '麦当劳'
    assert txns[0].pending == 0

def test_handle_wechat_expense(handler):
    result = handler.handle(
        'com.tencent.mm',
        '微信支付 18.00元 收款方：便利店'
    )
    assert result is True
    txns = handler.db.get_transactions()
    assert txns[0].source == 'wechat'

def test_handle_unrecognized_saves_pending(handler):
    # 无法解析的通知 → 返回 False，记入 pending
    result = handler.handle(
        'com.eg.android.AlipayGphone',
        '这是一条无法识别的通知内容'
    )
    assert result is False
    pending = handler.db.get_pending_transactions()
    assert len(pending) == 1
    assert pending[0].pending == 1

def test_handle_sets_timestamp(handler):
    handler.handle(
        'com.eg.android.AlipayGphone',
        '支付宝消息支出 10.00元 商家：测试商家',
        posted_at='2026-04-04T12:00:00'
    )
    txns = handler.db.get_transactions()
    assert txns[0].created_at == '2026-04-04T12:00:00'

def test_handle_auto_categorizes(handler):
    handler.handle(
        'com.eg.android.AlipayGphone',
        '支付宝消息支出 30.00元 商家：麦当劳'
    )
    txns = handler.db.get_transactions()
    # 麦当劳应该匹配到餐饮分类（category_id 不为 None）
    assert txns[0].category_id is not None


def test_handle_accessibility_source_upserts(handler):
    """无障碍来源应调用 upsert，合并 10s 内同金额记录"""
    # 先用通知路径插入一条
    handler.handle(
        'com.eg.android.AlipayGphone',
        '支付宝消息支出 25.50元 商家：未知',
        posted_at='2026-04-11T10:00:00',
        source='notification'
    )
    assert len(handler.db.get_transactions()) == 1

    # 无障碍路径 3 秒后到达
    handler.handle(
        'com.eg.android.AlipayGphone',
        '收款方\n麦当劳\n25.50\n支付成功',
        posted_at='2026-04-11T10:00:03',
        source='accessibility'
    )
    txns = handler.db.get_transactions()
    # 仍只有 1 条记录
    assert len(txns) == 1
    # 商家已更新
    assert txns[0].merchant == '麦当劳'
    assert txns[0].source == 'accessibility'


def test_handle_notification_source_always_inserts(handler):
    """通知来源始终新增，不做 upsert"""
    handler.handle(
        'com.eg.android.AlipayGphone',
        '支付宝消息支出 25.50元 商家：麦当劳',
        posted_at='2026-04-11T10:00:00',
        source='notification'
    )
    handler.handle(
        'com.eg.android.AlipayGphone',
        '支付宝消息支出 25.50元 商家：麦当劳',
        posted_at='2026-04-11T10:00:02',
        source='notification'
    )
    assert len(handler.db.get_transactions()) == 2


def test_handle_default_source_is_notification(handler):
    """不传 source 时默认走通知路径（始终 insert）"""
    handler.handle(
        'com.eg.android.AlipayGphone',
        '支付宝消息支出 10.00元 商家：测试'
    )
    txns = handler.db.get_transactions()
    assert len(txns) == 1
    assert txns[0].source in ('alipay', 'wechat', 'notification', 'manual')
