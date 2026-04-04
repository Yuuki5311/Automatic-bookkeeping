from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class ParseResult:
    amount: float
    type: str        # 'income' or 'expense'
    merchant: str
    source: str      # 'alipay' or 'wechat'


def parse_notification(package_name: str, text: str) -> Optional[ParseResult]:
    """
    解析通知文本。
    package_name: 'com.eg.android.AlipayGphone' 或 'com.tencent.mm'
    返回 ParseResult 或 None（无法解析时）
    """
    if 'alipay' in package_name.lower() or package_name == 'com.eg.android.AlipayGphone':
        return _parse_alipay(text)
    elif 'tencent.mm' in package_name or package_name == 'com.tencent.mm':
        return _parse_wechat(text)
    return None


def _parse_alipay(text: str) -> Optional[ParseResult]:
    """
    支付宝通知示例：
    - "支付宝消息支出 25.50元 商家：麦当劳"
    - "支付宝消息收入 100.00元 来源：转账"
    - "你已成功支付25.50元，收款方：星巴克"
    - "支付宝到账100元"
    """
    # 支出模式
    expense_patterns = [
        r'支出\s*([\d.]+)元.*?(?:商家|收款方)[：:]\s*(.+)',
        r'成功支付([\d.]+)元.*?(?:商家|收款方)[：:]\s*(.+)',
        r'付款([\d.]+)元.*?(?:给|商家|收款方)[：:\s]*(.+)',
    ]
    for pattern in expense_patterns:
        m = re.search(pattern, text)
        if m:
            return ParseResult(
                amount=float(m.group(1)),
                type='expense',
                merchant=m.group(2).strip(),
                source='alipay'
            )

    # 收入模式
    income_patterns = [
        r'收入\s*([\d.]+)元.*?(?:来源|付款方)[：:]\s*(.+)',
        r'到账([\d.]+)元',
    ]
    for pattern in income_patterns:
        m = re.search(pattern, text)
        if m:
            merchant = m.group(2).strip() if m.lastindex >= 2 else '转账'
            return ParseResult(
                amount=float(m.group(1)),
                type='income',
                merchant=merchant,
                source='alipay'
            )

    return None


def _parse_wechat(text: str) -> Optional[ParseResult]:
    """
    微信支付通知示例：
    - "微信支付 25.50元 收款方：便利店"
    - "微信支付成功，向便利店付款25.50元"
    - "你已收到25.50元转账"
    """
    # 支出模式
    expense_patterns = [
        r'微信支付\s*([\d.]+)元\s*收款方[：:]\s*(.+)',
        r'向(.+?)付款([\d.]+)元',
        r'付款([\d.]+)元.*?(?:给|收款方)[：:\s]*(.+)',
    ]
    for i, pattern in enumerate(expense_patterns):
        m = re.search(pattern, text)
        if m:
            if i == 1:  # "向XXX付款YY元" 模式，组顺序不同
                return ParseResult(
                    amount=float(m.group(2)),
                    type='expense',
                    merchant=m.group(1).strip(),
                    source='wechat'
                )
            return ParseResult(
                amount=float(m.group(1)),
                type='expense',
                merchant=m.group(2).strip(),
                source='wechat'
            )

    # 收入模式
    income_patterns = [
        r'收到([\d.]+)元转账',
        r'到账([\d.]+)元',
    ]
    for pattern in income_patterns:
        m = re.search(pattern, text)
        if m:
            return ParseResult(
                amount=float(m.group(1)),
                type='income',
                merchant='转账',
                source='wechat'
            )

    return None
