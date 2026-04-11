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
    if '\n' in text:
        res = _parse_accessibility(package_name, text)
        if res:
            return res

    if 'alipay' in package_name.lower() or package_name == 'com.eg.android.AlipayGphone':
        return _parse_alipay(text)
    elif 'tencent.mm' in package_name or package_name == 'com.tencent.mm':
        return _parse_wechat(text)
    return None

def _parse_accessibility(package_name: str, text: str) -> Optional[ParseResult]:
    source = 'alipay' if 'alipay' in package_name.lower() else 'wechat'
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    amount = 0.0
    merchant = '未知'
    type_ = 'expense' # Default to expense for accessibility payment pages

    amount_found = False
    merchant_found = False

    for i, line in enumerate(lines):
        # Look for amount
        if not amount_found:
            # Often amount is alone on a line, or "￥25.50", "-25.50", "25.50元"
            m = re.match(r'^[^\d]*?([\d]+\.\d{2})[^\d]*?$', line)
            if m:
                amount = float(m.group(1))
                amount_found = True
            elif line.replace('.', '', 1).isdigit() and '.' in line:
                amount = float(line)
                amount_found = True

        # Look for merchant
        if not merchant_found:
            if '收款方' in line or '商户' in line or '付款给' in line or '收款人' in line:
                # Sometimes it's on the same line: "收款方 星巴克" or "收款方星巴克"
                m = re.search(r'(?:收款方|商户.*?|付款给|收款人)[:：\s]*(.+)', line)
                if m and m.group(1).strip():
                    merchant = m.group(1).strip()
                    merchant_found = True
                elif i + 1 < len(lines):
                    # Next line is probably merchant
                    next_line = lines[i+1]
                    # Exclude lines that look like numbers or other labels
                    if not re.search(r'\d', next_line) and len(next_line) > 1:
                        merchant = next_line
                        merchant_found = True

    if amount > 0:
        return ParseResult(amount=amount, type=type_, merchant=merchant, source=source)
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
