import pytest
from src.models.transaction import Category
from src.core.categorizer import categorize


def _make_categories():
    return [
        Category(id=1, name='餐饮', icon='food', keywords='餐厅,外卖,美食,饭,咖啡,奶茶'),
        Category(id=2, name='交通', icon='car', keywords='滴滴,出租,地铁,公交,加油,停车'),
        Category(id=3, name='购物', icon='shopping', keywords='淘宝,京东,超市,商场,购物'),
        Category(id=4, name='其他', icon='dots', keywords=''),
    ]


def test_categorize_by_keyword():
    cats = _make_categories()
    result = categorize('麦当劳外卖', cats)
    assert result == 1  # 餐饮


def test_categorize_by_keyword_transport():
    cats = _make_categories()
    result = categorize('滴滴出行', cats)
    assert result == 2  # 交通


def test_categorize_by_keyword_shopping():
    cats = _make_categories()
    result = categorize('京东商城', cats)
    assert result == 3  # 购物


def test_categorize_fallback_to_other():
    cats = _make_categories()
    result = categorize('未知商家XYZ', cats)
    assert result == 4  # 其他


def test_categorize_case_insensitive():
    cats = [
        Category(id=1, name='咖啡', icon='coffee', keywords='starbucks,星巴克,咖啡'),
        Category(id=2, name='其他', icon='dots', keywords=''),
    ]
    result = categorize('Starbucks Reserve', cats)
    assert result == 1


def test_categorize_case_insensitive_mixed():
    cats = [
        Category(id=1, name='咖啡', icon='coffee', keywords='starbucks,星巴克,咖啡'),
        Category(id=2, name='其他', icon='dots', keywords=''),
    ]
    result = categorize('STARBUCKS', cats)
    assert result == 1


def test_categorize_empty_merchant():
    cats = _make_categories()
    result = categorize('', cats)
    assert result == 4  # 其他，无关键词匹配
