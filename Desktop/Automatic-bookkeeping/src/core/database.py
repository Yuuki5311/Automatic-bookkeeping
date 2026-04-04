import sqlite3
from pathlib import Path
from typing import Optional
from src.models.transaction import Transaction, Category

DEFAULT_CATEGORIES = [
    ('餐饮', 'food-fork-drink', '餐厅,外卖,美食,饭,咖啡,奶茶'),
    ('交通', 'car', '滴滴,出租,地铁,公交,加油,停车'),
    ('购物', 'shopping', '淘宝,京东,超市,商场,购物'),
    ('娱乐', 'gamepad-variant', '电影,游戏,KTV,娱乐'),
    ('医疗', 'hospital-box', '医院,药店,诊所,医疗'),
    ('转账', 'bank-transfer', '转账,还款,红包'),
    ('其他', 'dots-horizontal', ''),
]


class Database:
    def __init__(self, db_path: str = "bookkeeping.db"):
        self.db_path = db_path
        if db_path == ":memory:":
            self.conn = sqlite3.connect(":memory:")
            self.conn.row_factory = sqlite3.Row
        else:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.init_db()

    def init_db(self):
        cur = self.conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS categories (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                name     TEXT NOT NULL,
                icon     TEXT NOT NULL,
                keywords TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                amount      REAL    NOT NULL,
                type        TEXT    NOT NULL,
                category_id INTEGER REFERENCES categories(id),
                merchant    TEXT    NOT NULL DEFAULT '',
                note        TEXT    NOT NULL DEFAULT '',
                source      TEXT    NOT NULL DEFAULT 'manual',
                created_at  TEXT    NOT NULL,
                pending     INTEGER NOT NULL DEFAULT 1
            );
        """)
        row = cur.execute("SELECT COUNT(*) FROM categories").fetchone()
        if row[0] == 0:
            cur.executemany(
                "INSERT INTO categories (name, icon, keywords) VALUES (?, ?, ?)",
                DEFAULT_CATEGORIES,
            )
        self.conn.commit()

    # ------------------------------------------------------------------ #
    # Transaction CRUD
    # ------------------------------------------------------------------ #

    def add_transaction(self, t: Transaction) -> int:
        cur = self.conn.execute(
            """INSERT INTO transactions
               (amount, type, category_id, merchant, note, source, created_at, pending)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (t.amount, t.type, t.category_id, t.merchant,
             t.note, t.source, t.created_at, t.pending),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_transactions(self, limit: int = 50, offset: int = 0) -> list[Transaction]:
        rows = self.conn.execute(
            "SELECT * FROM transactions ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [self._row_to_transaction(r) for r in rows]

    def get_transaction(self, id: int) -> Optional[Transaction]:
        row = self.conn.execute(
            "SELECT * FROM transactions WHERE id = ?", (id,)
        ).fetchone()
        return self._row_to_transaction(row) if row else None

    def update_transaction(self, t: Transaction) -> None:
        self.conn.execute(
            """UPDATE transactions SET
               amount=?, type=?, category_id=?, merchant=?, note=?,
               source=?, created_at=?, pending=?
               WHERE id=?""",
            (t.amount, t.type, t.category_id, t.merchant,
             t.note, t.source, t.created_at, t.pending, t.id),
        )
        self.conn.commit()

    def delete_transaction(self, id: int) -> None:
        self.conn.execute("DELETE FROM transactions WHERE id = ?", (id,))
        self.conn.commit()

    def get_pending_transactions(self) -> list[Transaction]:
        rows = self.conn.execute(
            "SELECT * FROM transactions WHERE pending = 1 ORDER BY created_at DESC"
        ).fetchall()
        return [self._row_to_transaction(r) for r in rows]

    def get_monthly_summary(self, year: int, month: int) -> dict:
        prefix = f"{year:04d}-{month:02d}"
        rows = self.conn.execute(
            """SELECT type, SUM(amount) as total
               FROM transactions
               WHERE created_at LIKE ?
               GROUP BY type""",
            (f"{prefix}%",),
        ).fetchall()
        result = {'income': 0.0, 'expense': 0.0}
        for r in rows:
            if r['type'] in result:
                result[r['type']] = r['total']
        return result

    def get_category_summary(self, year: int, month: int) -> list[dict]:
        prefix = f"{year:04d}-{month:02d}"
        rows = self.conn.execute(
            """SELECT t.category_id, COALESCE(c.name, '未分类') as name,
                      SUM(t.amount) as total
               FROM transactions t
               LEFT JOIN categories c ON t.category_id = c.id
               WHERE t.type = 'expense' AND t.created_at LIKE ?
               GROUP BY t.category_id
               ORDER BY total DESC""",
            (f"{prefix}%",),
        ).fetchall()
        return [{'category_id': r['category_id'], 'name': r['name'], 'total': r['total']}
                for r in rows]

    def get_monthly_totals(self, months: int = 6) -> list[dict]:
        rows = self.conn.execute(
            """SELECT
                   CAST(strftime('%Y', created_at) AS INTEGER) as year,
                   CAST(strftime('%m', created_at) AS INTEGER) as month,
                   SUM(CASE WHEN type='income'  THEN amount ELSE 0 END) as income,
                   SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) as expense
               FROM transactions
               WHERE created_at >= date('now', ? || ' months')
               GROUP BY year, month
               ORDER BY year, month""",
            (f"-{months}",),
        ).fetchall()
        return [{'year': r['year'], 'month': r['month'],
                 'income': r['income'], 'expense': r['expense']}
                for r in rows]

    # ------------------------------------------------------------------ #
    # Category CRUD
    # ------------------------------------------------------------------ #

    def get_categories(self) -> list[Category]:
        rows = self.conn.execute("SELECT * FROM categories").fetchall()
        return [self._row_to_category(r) for r in rows]

    def get_category(self, id: int) -> Optional[Category]:
        row = self.conn.execute(
            "SELECT * FROM categories WHERE id = ?", (id,)
        ).fetchone()
        return self._row_to_category(row) if row else None

    def add_category(self, c: Category) -> int:
        cur = self.conn.execute(
            "INSERT INTO categories (name, icon, keywords) VALUES (?, ?, ?)",
            (c.name, c.icon, c.keywords),
        )
        self.conn.commit()
        return cur.lastrowid

    def update_category(self, c: Category) -> None:
        self.conn.execute(
            "UPDATE categories SET name=?, icon=?, keywords=? WHERE id=?",
            (c.name, c.icon, c.keywords, c.id),
        )
        self.conn.commit()

    def delete_category(self, id: int) -> None:
        self.conn.execute("DELETE FROM categories WHERE id = ?", (id,))
        self.conn.commit()

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _row_to_transaction(row) -> Transaction:
        return Transaction(
            id=row['id'],
            amount=row['amount'],
            type=row['type'],
            category_id=row['category_id'],
            merchant=row['merchant'],
            note=row['note'],
            source=row['source'],
            created_at=row['created_at'],
            pending=row['pending'],
        )

    @staticmethod
    def _row_to_category(row) -> Category:
        return Category(
            id=row['id'],
            name=row['name'],
            icon=row['icon'],
            keywords=row['keywords'],
        )
