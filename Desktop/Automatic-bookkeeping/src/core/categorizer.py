from src.models.transaction import Category


def categorize(merchant: str, categories: list[Category]) -> int:
    """
    根据商家名称匹配分类，返回 category_id。
    匹配规则：遍历 categories，检查 merchant 是否包含任意关键词。
    无匹配时返回"其他"分类的 id（name == '其他'）。
    """
    merchant_lower = merchant.lower()
    other_id = None

    for cat in categories:
        if cat.name == '其他':
            other_id = cat.id
            continue
        for kw in cat.keyword_list():
            if kw and kw in merchant_lower:
                return cat.id

    return other_id  # 兜底返回"其他"
