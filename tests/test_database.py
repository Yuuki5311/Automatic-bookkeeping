import pytest
from src.core.database import Database
from src.models.transaction import Transaction, Category


def make_db() -> Database:
    db = Database(":memory:")
    return db


def sample_transaction(**kwargs) -> Transaction:
    defaults = dict(
        id=None,
        amount=100.0,
        type='expense',
        category_id=1,
        merchant='测试商家',
        note='',
        source='manual',
        created_at='2026-04-04T13:00:00',
        pending=0,
    )
    defaults.update(kwargs)
    return Transaction(**defaults)


# ------------------------------------------------------------------ #

def test_init_creates_tables():
    db = make_db()
    cats = db.get_categories()
    assert len(cats) == 7
    names = [c.name for c in cats]
    assert '餐饮' in names
    assert '其他' in names


def test_add_and_get_transaction():
    db = make_db()
    t = sample_transaction(amount=88.5, merchant='星巴克')
    new_id = db.add_transaction(t)
    assert new_id is not None and new_id > 0

    fetched = db.get_transaction(new_id)
    assert fetched is not None
    assert fetched.amount == 88.5
    assert fetched.merchant == '星巴克'
    assert fetched.id == new_id


def test_update_transaction():
    db = make_db()
    t = sample_transaction(amount=50.0, note='原始备注')
    tid = db.add_transaction(t)

    fetched = db.get_transaction(tid)
    fetched.amount = 99.9
    fetched.note = '已修改'
    db.update_transaction(fetched)

    updated = db.get_transaction(tid)
    assert updated.amount == 99.9
    assert updated.note == '已修改'


def test_delete_transaction():
    db = make_db()
    tid = db.add_transaction(sample_transaction())
    assert db.get_transaction(tid) is not None

    db.delete_transaction(tid)
    assert db.get_transaction(tid) is None


def test_get_pending_transactions():
    db = make_db()
    db.add_transaction(sample_transaction(pending=1, merchant='待分类A'))
    db.add_transaction(sample_transaction(pending=1, merchant='待分类B'))
    db.add_transaction(sample_transaction(pending=0, merchant='已分类'))

    pending = db.get_pending_transactions()
    assert len(pending) == 2
    merchants = {p.merchant for p in pending}
    assert '待分类A' in merchants
    assert '待分类B' in merchants
    assert '已分类' not in merchants


def test_monthly_summary():
    db = make_db()
    db.add_transaction(sample_transaction(amount=200.0, type='income',  created_at='2026-04-01T10:00:00'))
    db.add_transaction(sample_transaction(amount=150.0, type='expense', created_at='2026-04-02T10:00:00'))
    db.add_transaction(sample_transaction(amount=50.0,  type='expense', created_at='2026-04-03T10:00:00'))
    db.add_transaction(sample_transaction(amount=999.0, type='expense', created_at='2026-03-31T10:00:00'))

    summary = db.get_monthly_summary(2026, 4)
    assert summary['income'] == pytest.approx(200.0)
    assert summary['expense'] == pytest.approx(200.0)


def test_category_summary():
    db = make_db()
    cats = db.get_categories()
    cat1 = cats[0]  # 餐饮
    cat2 = cats[1]  # 交通

    db.add_transaction(sample_transaction(amount=80.0,  category_id=cat1.id, created_at='2026-04-01T10:00:00'))
    db.add_transaction(sample_transaction(amount=120.0, category_id=cat1.id, created_at='2026-04-02T10:00:00'))
    db.add_transaction(sample_transaction(amount=30.0,  category_id=cat2.id, created_at='2026-04-03T10:00:00'))
    # income should be excluded
    db.add_transaction(sample_transaction(amount=500.0, type='income', category_id=cat1.id, created_at='2026-04-04T10:00:00'))

    result = db.get_category_summary(2026, 4)
    assert len(result) == 2
    # sorted by total desc: 餐饮(200) > 交通(30)
    assert result[0]['name'] == cat1.name
    assert result[0]['total'] == pytest.approx(200.0)
    assert result[1]['name'] == cat2.name
    assert result[1]['total'] == pytest.approx(30.0)


def test_get_monthly_totals():
    db = make_db()
    db.add_transaction(sample_transaction(amount=300.0, type='income',  created_at='2026-04-01T10:00:00'))
    db.add_transaction(sample_transaction(amount=100.0, type='expense', created_at='2026-04-02T10:00:00'))
    db.add_transaction(sample_transaction(amount=200.0, type='income',  created_at='2026-03-15T10:00:00'))

    totals = db.get_monthly_totals(months=6)
    assert len(totals) >= 2

    apr = next((r for r in totals if r['year'] == 2026 and r['month'] == 4), None)
    assert apr is not None
    assert apr['income'] == pytest.approx(300.0)
    assert apr['expense'] == pytest.approx(100.0)

    mar = next((r for r in totals if r['year'] == 2026 and r['month'] == 3), None)
    assert mar is not None
    assert mar['income'] == pytest.approx(200.0)


def test_upsert_transaction_updates_existing_within_window():
    """无障碍数据在 10s 内到达，应更新已有记录而非新增"""
    db = make_db()
    t1 = sample_transaction(
        amount=25.50, type='expense', merchant='未知',
        source='notification', created_at='2026-04-11T10:00:00', pending=0
    )
    tid = db.add_transaction(t1)

    t2 = sample_transaction(
        amount=25.50, type='expense', merchant='麦当劳',
        source='accessibility', created_at='2026-04-11T10:00:05', pending=0
    )
    result_id = db.upsert_transaction(t2, window_seconds=10)

    assert result_id == tid
    updated = db.get_transaction(tid)
    assert updated.merchant == '麦当劳'
    assert updated.source == 'accessibility'
    assert len(db.get_transactions()) == 1


def test_upsert_transaction_inserts_when_no_match():
    """无障碍数据在窗口外，应新增记录"""
    db = make_db()
    t1 = sample_transaction(
        amount=25.50, type='expense', merchant='未知',
        source='notification', created_at='2026-04-11T10:00:00', pending=0
    )
    tid = db.add_transaction(t1)

    t2 = sample_transaction(
        amount=25.50, type='expense', merchant='麦当劳',
        source='accessibility', created_at='2026-04-11T10:00:15', pending=0
    )
    result_id = db.upsert_transaction(t2, window_seconds=10)

    assert result_id is not None and result_id > 0
    assert result_id != tid
    assert len(db.get_transactions()) == 2


def test_upsert_transaction_does_not_merge_different_amounts():
    """金额不同的两条记录不应合并"""
    db = make_db()
    t1 = sample_transaction(
        amount=25.50, type='expense', merchant='未知',
        source='notification', created_at='2026-04-11T10:00:00', pending=0
    )
    db.add_transaction(t1)

    t2 = sample_transaction(
        amount=30.00, type='expense', merchant='星巴克',
        source='accessibility', created_at='2026-04-11T10:00:03', pending=0
    )
    db.upsert_transaction(t2, window_seconds=10)

    assert len(db.get_transactions()) == 2
