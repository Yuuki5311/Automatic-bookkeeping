from dataclasses import dataclass
from typing import Optional


@dataclass
class Category:
    id: Optional[int]
    name: str
    icon: str
    keywords: str  # 逗号分隔

    def keyword_list(self) -> list[str]:
        return [k.strip() for k in self.keywords.split(',') if k.strip()]


@dataclass
class Transaction:
    id: Optional[int]
    amount: float
    type: str  # 'income' or 'expense'
    category_id: Optional[int]
    merchant: str
    note: str
    source: str  # 'alipay', 'wechat', 'manual'
    created_at: str  # ISO8601
    pending: int  # 0 or 1
