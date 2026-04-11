import pytest
from src.core.parser import parse_notification, ParseResult


ALIPAY_PKG = 'com.eg.android.AlipayGphone'
WECHAT_PKG = 'com.tencent.mm'


def test_parse_alipay_expense():
    text = '支付宝消息支出 25.50元 商家：麦当劳'
    result = parse_notification(ALIPAY_PKG, text)
    assert result is not None
    assert result.amount == 25.50
    assert result.type == 'expense'
    assert result.merchant == '麦当劳'
    assert result.source == 'alipay'


def test_parse_alipay_expense_alternate():
    text = '你已成功支付25.50元，收款方：星巴克'
    result = parse_notification(ALIPAY_PKG, text)
    assert result is not None
    assert result.amount == 25.50
    assert result.type == 'expense'
    assert result.merchant == '星巴克'
    assert result.source == 'alipay'


def test_parse_alipay_income():
    text = '支付宝消息收入 100.00元 来源：转账'
    result = parse_notification(ALIPAY_PKG, text)
    assert result is not None
    assert result.amount == 100.00
    assert result.type == 'income'
    assert result.merchant == '转账'
    assert result.source == 'alipay'


def test_parse_alipay_income_daodao():
    text = '支付宝到账100元'
    result = parse_notification(ALIPAY_PKG, text)
    assert result is not None
    assert result.amount == 100.0
    assert result.type == 'income'
    assert result.merchant == '转账'
    assert result.source == 'alipay'


def test_parse_wechat_expense():
    text = '微信支付 25.50元 收款方：便利店'
    result = parse_notification(WECHAT_PKG, text)
    assert result is not None
    assert result.amount == 25.50
    assert result.type == 'expense'
    assert result.merchant == '便利店'
    assert result.source == 'wechat'


def test_parse_wechat_expense_xiang():
    text = '微信支付成功，向便利店付款25.50元'
    result = parse_notification(WECHAT_PKG, text)
    assert result is not None
    assert result.amount == 25.50
    assert result.type == 'expense'
    assert result.merchant == '便利店'
    assert result.source == 'wechat'


def test_parse_wechat_income():
    text = '你已收到25.50元转账'
    result = parse_notification(WECHAT_PKG, text)
    assert result is not None
    assert result.amount == 25.50
    assert result.type == 'income'
    assert result.merchant == '转账'
    assert result.source == 'wechat'


def test_parse_unknown_package():
    result = parse_notification('com.unknown.app', '支出 25.50元 商家：麦当劳')
    assert result is None


def test_parse_unrecognized_text():
    text = '这是一条无法识别的通知消息'
    result = parse_notification(ALIPAY_PKG, text)
    assert result is None


def test_parse_unrecognized_wechat_text():
    text = '这是一条无法识别的微信通知'
    result = parse_notification(WECHAT_PKG, text)
    assert result is None

def test_parse_accessibility_wechat():
    text = "支付成功\n25.50\n收款方\n便利店\n完成"
    result = parse_notification(WECHAT_PKG, text)
    assert result is not None
    assert result.amount == 25.50
    assert result.type == "expense"
    assert result.merchant == "便利店"
    assert result.source == "wechat"

def test_parse_accessibility_alipay():
    text = "交易成功\n-25.50\n付款给 星巴克"
    result = parse_notification(ALIPAY_PKG, text)
    assert result is not None
    assert result.amount == 25.50
    assert result.type == "expense"
    assert result.merchant == "星巴克"
    assert result.source == "alipay"

