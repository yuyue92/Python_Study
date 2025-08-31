# -*- coding: utf-8 -*-
"""
Inventory Management Desktop (PyQt5 + sqlite3, Python 3.8)

功能：
- 顶部菜单（快捷键）、顶部工具条（搜索/动作/用户状态）、底部状态栏
- 左侧树形菜单导航（图标+文字，可展开）
- 右侧多页面（仪表板/商品管理/入库/出库/事务记录/设置），QStackedWidget 切换
- 本地 sqlite3 存储（自动建库建表，首跑注入示例数据）
- 商品管理（增/改/删、搜索、低库存标色）
- 入库/出库（校验、原子事务、更新库存）
- 事务记录（筛选：日期/商品/类型；导出 CSV）
- 设置（主题切换、数据库备份）

文件：
- 默认数据库 inventoryManage.db 与脚本同目录
"""

import os
import sys
import csv
import shutil
import sqlite3
from datetime import datetime, timedelta

from PyQt5.QtCore import Qt, QSize, QDate
from PyQt5.QtGui import QIcon, QPalette, QColor, QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTreeWidget, QTreeWidgetItem,
    QStackedWidget, QSplitter, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QFormLayout, QLineEdit,
    QDoubleSpinBox, QSpinBox, QComboBox, QPushButton, QGroupBox, QAction,
    QToolBar, QStatusBar, QFileDialog, QMessageBox, QStyle, QSizePolicy,
    QHeaderView, QDateEdit, QDialog, QDialogButtonBox
)

APP_TITLE = "库存管理系统 / Inventory Suite"
DB_FILE = "inventoryManage.db"


# ---------------------------
# 主题
# ---------------------------
def apply_dark_theme(app: QApplication):
    app.setStyle("Fusion")
    palette = QPalette()
    base = QColor(30, 30, 30)
    window = QColor(36, 36, 36)
    alt_base = QColor(45, 45, 45)
    text = QColor(230, 230, 230)
    disabled_text = QColor(140, 140, 140)
    highlight = QColor(53, 132, 228)
    highlight_text = QColor(255, 255, 255)
    button = QColor(50, 50, 50)
    link = QColor(84, 160, 255)

    palette.setColor(QPalette.Window, window)
    palette.setColor(QPalette.WindowText, text)
    palette.setColor(QPalette.Base, base)
    palette.setColor(QPalette.AlternateBase, alt_base)
    palette.setColor(QPalette.Text, text)
    palette.setColor(QPalette.Disabled, QPalette.Text, disabled_text)
    palette.setColor(QPalette.ToolTipBase, window)
    palette.setColor(QPalette.ToolTipText, text)
    palette.setColor(QPalette.Button, button)
    palette.setColor(QPalette.ButtonText, text)
    palette.setColor(QPalette.BrightText, highlight_text)
    palette.setColor(QPalette.Link, link)
    palette.setColor(QPalette.Highlight, highlight)
    palette.setColor(QPalette.HighlightedText, highlight_text)
    app.setPalette(palette)
    app.setStyleSheet("""
        QWidget { font-size: 13px; }
        QGroupBox { 
            border: 1px solid #3f3f3f; 
            border-radius: 12px; 
            margin-top: 14px; 
            padding: 10px; 
        }
        QGroupBox::title { 
            subcontrol-origin: margin; 
            left: 12px; 
            padding: 0 4px; 
        }
        QTreeWidget { border-right: 1px solid #3f3f3f; }
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {
            border: 1px solid #4a4a4a; border-radius: 8px; padding: 6px; background: #2b2b2b;
        }
        QPushButton {
            border: 1px solid #4a4a4a; border-radius: 10px; padding: 8px 12px; background: #3b3b3b;
        }
        QPushButton:hover { background: #4a4a4a; }
        QPushButton:pressed { background: #2f2f2f; }
        QToolBar { background: #2b2b2b; border-bottom: 1px solid #3f3f3f; padding: 4px; }
        QStatusBar { background: #2b2b2b; border-top: 1px solid #3f3f3f; }
        QHeaderView::section { background: #2f2f2f; padding: 6px; border: none; }
        QTableWidget { gridline-color: #404040; selection-background-color: #3568d4; }
    """)


def apply_light_theme(app: QApplication):
    app.setStyle("Fusion")
    app.setPalette(app.style().standardPalette())
    app.setStyleSheet("""
        QWidget { font-size: 13px; }
        QGroupBox { 
            border: 1px solid #dcdcdc; border-radius: 12px; margin-top: 14px; padding: 10px; 
        }
        QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; }
        QToolBar { background: #f6f6f6; }
        QStatusBar { background: #f6f6f6; }
    """)


# ---------------------------
# 数据库
# ---------------------------
class Database:
    def __init__(self, path: str):
        self.path = path
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.conn.execute("PRAGMA journal_mode = WAL;")
        self.init_schema()

    def init_schema(self):
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT,
            unit TEXT DEFAULT '件',
            price REAL DEFAULT 0,
            stock REAL DEFAULT 0,
            min_stock REAL DEFAULT 0,
            active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('IN','OUT','ADJ')),
            quantity REAL NOT NULL,
            unit_price REAL DEFAULT 0,
            reference TEXT,
            note TEXT,
            ts TEXT DEFAULT (datetime('now','localtime')),
            user TEXT,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        );
        """)
        self.conn.commit()
        # 首次运行注入示例
        cur.execute("SELECT COUNT(*) FROM products;")
        if cur.fetchone()[0] == 0:
            demo = [
                ("SKU-1001", "蓝牙耳机", "数码", "件", 199.0, 120, 10, 1),
                ("SKU-1002", "机械键盘", "外设", "件", 399.0, 35, 5, 1),
                ("SKU-1003", "27寸显示器", "显示设备", "件", 1699.0, 12, 2, 1),
                ("SKU-1004", "C to C 数据线", "配件", "条", 29.9, 500, 50, 1),
            ]
            cur.executemany("""
                INSERT INTO products (sku,name,category,unit,price,stock,min_stock,active)
                VALUES (?,?,?,?,?,?,?,?)
            """, demo)
            self.conn.commit()

    # ---- 商品 ----
    def list_products(self, keyword: str = ""):
        kw = f"%{keyword.strip()}%" if keyword else "%"
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id, sku, name, category, unit, price, stock, min_stock, active, created_at
            FROM products
            WHERE (sku LIKE ? OR name LIKE ? OR category LIKE ?) 
            ORDER BY id DESC
        """, (kw, kw, kw))
        return cur.fetchall()

    def get_product(self, pid: int):
        cur = self.conn.cursor()
        cur.execute("SELECT id, sku, name, category, unit, price, stock, min_stock, active FROM products WHERE id=?", (pid,))
        return cur.fetchone()

    def add_product(self, sku, name, category, unit, price, min_stock, active=1):
        with self.conn:
            self.conn.execute("""
                INSERT INTO products (sku,name,category,unit,price,min_stock,active)
                VALUES (?,?,?,?,?,?,?)
            """, (sku, name, category, unit, price, min_stock, active))

    def update_product(self, pid, sku, name, category, unit, price, min_stock, active):
        with self.conn:
            self.conn.execute("""
                UPDATE products SET sku=?, name=?, category=?, unit=?, price=?, min_stock=?, active=?, updated_at=datetime('now','localtime')
                WHERE id=?
            """, (sku, name, category, unit, price, min_stock, active, pid))

    def delete_product(self, pid):
        with self.conn:
            self.conn.execute("DELETE FROM products WHERE id=?", (pid,))

    # ---- 事务 ----
    def stock_in(self, product_id: int, qty: float, unit_price: float = 0.0, ref: str = "", note: str = "", user: str = "Admin"):
        if qty <= 0:
            raise ValueError("数量必须大于 0")
        with self.conn:
            self.conn.execute("""
                INSERT INTO transactions (product_id, type, quantity, unit_price, reference, note, user)
                VALUES (?, 'IN', ?, ?, ?, ?, ?)
            """, (product_id, qty, unit_price, ref, note, user))
            self.conn.execute("UPDATE products SET stock = stock + ?, updated_at=datetime('now','localtime') WHERE id=?",
                              (qty, product_id))

    def stock_out(self, product_id: int, qty: float, unit_price: float = 0.0, ref: str = "", note: str = "", user: str = "Admin"):
        if qty <= 0:
            raise ValueError("数量必须大于 0")
        cur = self.conn.cursor()
        cur.execute("SELECT stock FROM products WHERE id=?", (product_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError("商品不存在")
        if row[0] < qty:
            raise ValueError("库存不足，无法出库")
        with self.conn:
            self.conn.execute("""
                INSERT INTO transactions (product_id, type, quantity, unit_price, reference, note, user)
                VALUES (?, 'OUT', ?, ?, ?, ?, ?)
            """, (product_id, qty, unit_price, ref, note, user))
            self.conn.execute("UPDATE products SET stock = stock - ?, updated_at=datetime('now','localtime') WHERE id=?",
                              (qty, product_id))

    def list_transactions(self, start_date: str = None, end_date: str = None, product_id: int = None, typ: str = None):
        sql = """
            SELECT t.id, t.ts, 
                   CASE t.type WHEN 'IN' THEN '入库' WHEN 'OUT' THEN '出库' ELSE t.type END AS type_name,
                   p.sku, p.name, t.quantity, p.unit, t.unit_price, t.reference, t.note, t.user, t.product_id
            FROM transactions t
            JOIN products p ON p.id = t.product_id
            WHERE 1=1
        """
        params = []
        if start_date:
            sql += " AND date(t.ts) >= date(?)"
            params.append(start_date)
        if end_date:
            sql += " AND date(t.ts) <= date(?)"
            params.append(end_date)
        if product_id:
            sql += " AND t.product_id=?"
            params.append(product_id)
        if typ in ("IN", "OUT"):
            sql += " AND t.type=?"
            params.append(typ)
        sql += " ORDER BY t.ts DESC, t.id DESC"
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()

    def kpi(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*), IFNULL(SUM(stock),0) FROM products WHERE active=1")
        prod_count, total_stock = cur.fetchone()
        cur.execute("""
            SELECT COUNT(*) FROM products WHERE active=1 AND stock <= min_stock
        """)
        low = cur.fetchone()[0]
        cur.execute("""
            SELECT t.ts, p.name, t.type, t.quantity, p.unit 
            FROM transactions t JOIN products p ON p.id=t.product_id
            ORDER BY t.ts DESC LIMIT 8
        """)
        recent = cur.fetchall()
        return prod_count, total_stock, low, recent

    def product_options(self, only_active=True):
        cur = self.conn.cursor()
        if only_active:
            cur.execute("SELECT id, sku, name FROM products WHERE active=1 ORDER BY name")
        else:
            cur.execute("SELECT id, sku, name FROM products ORDER BY name")
        return cur.fetchall()


# ---------------------------
# 商品编辑对话框
# ---------------------------
class ProductDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("商品信息")
        self.resize(420, 280)
        form = QFormLayout(self)

        self.ed_sku = QLineEdit()
        self.ed_name = QLineEdit()
        self.ed_cat = QLineEdit()
        self.ed_unit = QLineEdit("件")
        self.sp_price = QDoubleSpinBox(); self.sp_price.setRange(0, 1e9); self.sp_price.setDecimals(2); self.sp_price.setValue(0.0)
        self.sp_min = QDoubleSpinBox(); self.sp_min.setRange(0, 1e9); self.sp_min.setDecimals(2); self.sp_min.setValue(0.0)
        self.cb_active = QComboBox(); self.cb_active.addItems(["停用", "启用"]); self.cb_active.setCurrentIndex(1)

        form.addRow("SKU：", self.ed_sku)
        form.addRow("名称：", self.ed_name)
        form.addRow("类别：", self.ed_cat)
        form.addRow("单位：", self.ed_unit)
        form.addRow("单价：", self.sp_price)
        form.addRow("最低库存：", self.sp_min)
        form.addRow("状态：", self.cb_active)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

        self._data = data
        if data:
            # data: (id, sku, name, category, unit, price, stock, min_stock, active)
            _, sku, name, cat, unit, price, stock, min_stock, active = data
            self.ed_sku.setText(sku)
            self.ed_name.setText(name)
            self.ed_cat.setText(cat or "")
            self.ed_unit.setText(unit or "件")
            self.sp_price.setValue(float(price or 0))
            self.sp_min.setValue(float(min_stock or 0))
            self.cb_active.setCurrentIndex(1 if int(active or 0) == 1 else 0)

    def get_values(self):
        return dict(
            sku=self.ed_sku.text().strip(),
            name=self.ed_name.text().strip(),
            category=self.ed_cat.text().strip(),
            unit=self.ed_unit.text().strip() or "件",
            price=float(self.sp_price.value()),
            min_stock=float(self.sp_min.value()),
            active=1 if self.cb_active.currentIndex() == 1 else 0
        )


# ---------------------------
# 页面：仪表板
# ---------------------------
class DashboardPage(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        main = QVBoxLayout(self); main.setContentsMargins(12, 12, 12, 12); main.setSpacing(12)

        kpi_row = QHBoxLayout(); kpi_row.setSpacing(12)
        self.card_products = self._kpi_card("在册商品", "0")
        self.card_stock = self._kpi_card("库存总量", "0")
        self.card_low = self._kpi_card("低库存", "0")
        kpi_row.addWidget(self.card_products); kpi_row.addWidget(self.card_stock); kpi_row.addWidget(self.card_low)
        main.addLayout(kpi_row)

        recent = QGroupBox("最近事务")
        v = QVBoxLayout(recent)
        self.list_recent = QListWidget()
        v.addWidget(self.list_recent)
        main.addWidget(recent)

        self.refresh()

    def _kpi_card(self, title, value):
        g = QGroupBox(title)
        lab = QLabel(value); lab.setAlignment(Qt.AlignCenter); f = lab.font(); f.setPointSize(24); f.setBold(True); lab.setFont(f)
        lay = QVBoxLayout(g); lay.addWidget(lab)
        g.value_label = lab
        return g

    def refresh(self):
        prod_count, total_stock, low, recent = self.db.kpi()
        self.card_products.value_label.setText(str(prod_count))
        self.card_stock.value_label.setText(f"{total_stock:g}")
        self.card_low.value_label.setText(str(low))
        self.list_recent.clear()
        for ts, name, typ, qty, unit in recent:
            tname = "入库" if typ == "IN" else ("出库" if typ == "OUT" else typ)
            self.list_recent.addItem(f"{ts} · {name} · {tname} {qty:g}{unit}")


# ---------------------------
# 页面：商品管理
# ---------------------------
class ProductsPage(QWidget):
    def __init__(self, db: Database, on_data_changed):
        super().__init__()
        self.db = db
        self.on_data_changed = on_data_changed

        outer = QVBoxLayout(self); outer.setContentsMargins(12, 12, 12, 12); outer.setSpacing(12)

        # 顶部：搜索+按钮
        top = QHBoxLayout()
        self.ed_search = QLineEdit(); self.ed_search.setPlaceholderText("搜索 SKU/名称/类别…")
        self.ed_search.textChanged.connect(self.refresh)
        btn_add = QPushButton("新增商品"); btn_add.clicked.connect(self.add_item)
        btn_edit = QPushButton("编辑选中"); btn_edit.clicked.connect(self.edit_item)
        btn_del = QPushButton("删除选中"); btn_del.clicked.connect(self.delete_item)
        btn_refresh = QPushButton("刷新"); btn_refresh.clicked.connect(self.refresh)
        top.addWidget(self.ed_search); top.addStretch(); top.addWidget(btn_add); top.addWidget(btn_edit); top.addWidget(btn_del); top.addWidget(btn_refresh)

        # 表格
        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels(["ID", "SKU", "名称", "类别", "单位", "单价", "库存", "最低", "状态", "创建时间"])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)

        outer.addLayout(top)
        outer.addWidget(self.table)
        self.refresh()

    def refresh(self):
        kw = self.ed_search.text().strip()
        rows = self.db.list_products(kw)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            # row: id, sku, name, cat, unit, price, stock, min_stock, active, created_at
            for c, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                if c in (0, 5, 6, 7):  # 数值靠右
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.table.setItem(r, c, item)
            # 低库存标色
            stock = float(row[6] or 0)
            min_stock = float(row[7] or 0)
            if stock <= min_stock:
                for c in range(self.table.columnCount()):
                    self.table.item(r, c).setBackground(QColor(64, 24, 24))
        self.table.setSortingEnabled(True)

    def selected_product_id(self):
        sel = self.table.selectedItems()
        if not sel: return None
        row = sel[0].row()
        return int(self.table.item(row, 0).text())

    def add_item(self):
        dlg = ProductDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            v = dlg.get_values()
            if not v["sku"] or not v["name"]:
                QMessageBox.warning(self, "提示", "SKU 与 名称 不能为空")
                return
            try:
                self.db.add_product(v["sku"], v["name"], v["category"], v["unit"], v["price"], v["min_stock"], v["active"])
                self.refresh(); self.on_data_changed()
            except sqlite3.IntegrityError as e:
                QMessageBox.warning(self, "失败", f"SKU 可能重复：{e}")

    def edit_item(self):
        pid = self.selected_product_id()
        if not pid:
            QMessageBox.information(self, "提示", "请先选择一行")
            return
        data = self.db.get_product(pid)
        dlg = ProductDialog(self, data=data)
        if dlg.exec_() == QDialog.Accepted:
            v = dlg.get_values()
            if not v["sku"] or not v["name"]:
                QMessageBox.warning(self, "提示", "SKU 与 名称 不能为空")
                return
            try:
                self.db.update_product(pid, v["sku"], v["name"], v["category"], v["unit"], v["price"], v["min_stock"], v["active"])
                self.refresh(); self.on_data_changed()
            except sqlite3.IntegrityError as e:
                QMessageBox.warning(self, "失败", f"SKU 可能重复：{e}")

    def delete_item(self):
        pid = self.selected_product_id()
        if not pid:
            QMessageBox.information(self, "提示", "请先选择一行")
            return
        if QMessageBox.question(self, "确认", "删除后将无法恢复，且会删除该商品的所有事务记录，确认？") == QMessageBox.Yes:
            try:
                self.db.delete_product(pid)
                self.refresh(); self.on_data_changed()
            except Exception as e:
                QMessageBox.warning(self, "失败", str(e))


# ---------------------------
# 页面：入库
# ---------------------------
class StockInPage(QWidget):
    def __init__(self, db: Database, notify_refresh_all):
        super().__init__()
        self.db = db
        self.notify_refresh_all = notify_refresh_all
        outer = QVBoxLayout(self); outer.setContentsMargins(12, 12, 12, 12); outer.setSpacing(12)

        form_g = QGroupBox("入库单")
        form = QFormLayout(form_g)
        self.cb_prod = QComboBox(); self.reload_products()
        self.sp_qty = QDoubleSpinBox(); self.sp_qty.setRange(0, 1e12); self.sp_qty.setDecimals(3); self.sp_qty.setValue(1.0)
        self.sp_price = QDoubleSpinBox(); self.sp_price.setRange(0, 1e12); self.sp_price.setDecimals(2); self.sp_price.setValue(0.0)
        self.ed_ref = QLineEdit(); self.ed_ref.setPlaceholderText("单据号/来源…")
        self.ed_note = QLineEdit(); self.ed_note.setPlaceholderText("备注…")
        btn = QPushButton("确认入库"); btn.clicked.connect(self.do_in)

        form.addRow("商品：", self.cb_prod)
        form.addRow("数量：", self.sp_qty)
        form.addRow("单价：", self.sp_price)
        form.addRow("参考号：", self.ed_ref)
        form.addRow("备注：", self.ed_note)
        form.addRow(btn)

        # 右侧：当前库存 / 最近入库
        right = QGroupBox("参考信息")
        v = QVBoxLayout(right)
        self.lab_stock = QLabel("当前库存：—")
        v.addWidget(self.lab_stock)
        self.list_recent = QListWidget()
        v.addWidget(self.list_recent)

        # 响应式
        split = QSplitter()
        split.addWidget(form_g)
        split.addWidget(right)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 2)

        outer.addWidget(split)

        self.cb_prod.currentIndexChanged.connect(self._update_info)
        self._update_info()

    def reload_products(self):
        self.cb_prod.blockSignals(True)
        self.cb_prod.clear()
        for pid, sku, name in self.db.product_options(True):
            self.cb_prod.addItem(f"{name} ({sku})", pid)
        self.cb_prod.blockSignals(False)

    def _update_info(self):
        pid = self.cb_prod.currentData()
        if not pid:
            self.lab_stock.setText("当前库存：—"); self.list_recent.clear(); return
        p = self.db.get_product(pid)
        if p:
            stock = float(p[6] or 0); unit = p[4] or "件"
            self.lab_stock.setText(f"当前库存：{stock:g} {unit}")
        # 最近入库记录
        rows = self.db.list_transactions(product_id=pid, typ="IN")
        self.list_recent.clear()
        for r in rows[:8]:
            _id, ts, type_name, sku, name, qty, unit, price, ref, note, user, _pid = r
            self.list_recent.addItem(f"{ts} · +{qty:g}{unit} @ {price:.2f} · {ref or ''}")

    def do_in(self):
        pid = self.cb_prod.currentData()
        if not pid:
            QMessageBox.warning(self, "提示", "请选择商品")
            return
        try:
            self.db.stock_in(
                product_id=pid,
                qty=float(self.sp_qty.value()),
                unit_price=float(self.sp_price.value()),
                ref=self.ed_ref.text().strip(),
                note=self.ed_note.text().strip(),
                user="Admin"
            )
            QMessageBox.information(self, "成功", "入库完成")
            self._update_info()
            self.notify_refresh_all()
        except Exception as e:
            QMessageBox.warning(self, "失败", str(e))


# ---------------------------
# 页面：出库
# ---------------------------
class StockOutPage(QWidget):
    def __init__(self, db: Database, notify_refresh_all):
        super().__init__()
        self.db = db
        self.notify_refresh_all = notify_refresh_all
        outer = QVBoxLayout(self); outer.setContentsMargins(12, 12, 12, 12); outer.setSpacing(12)

        form_g = QGroupBox("出库单")
        form = QFormLayout(form_g)
        self.cb_prod = QComboBox(); self.reload_products()
        self.sp_qty = QDoubleSpinBox(); self.sp_qty.setRange(0, 1e12); self.sp_qty.setDecimals(3); self.sp_qty.setValue(1.0)
        self.sp_price = QDoubleSpinBox(); self.sp_price.setRange(0, 1e12); self.sp_price.setDecimals(2); self.sp_price.setValue(0.0)
        self.ed_ref = QLineEdit(); self.ed_ref.setPlaceholderText("单据号/去向…")
        self.ed_note = QLineEdit(); self.ed_note.setPlaceholderText("备注…")
        btn = QPushButton("确认出库"); btn.clicked.connect(self.do_out)

        form.addRow("商品：", self.cb_prod)
        form.addRow("数量：", self.sp_qty)
        form.addRow("单价：", self.sp_price)
        form.addRow("参考号：", self.ed_ref)
        form.addRow("备注：", self.ed_note)
        form.addRow(btn)

        right = QGroupBox("参考信息")
        v = QVBoxLayout(right)
        self.lab_stock = QLabel("当前库存：—")
        v.addWidget(self.lab_stock)
        self.list_recent = QListWidget()
        v.addWidget(self.list_recent)

        split = QSplitter()
        split.addWidget(form_g)
        split.addWidget(right)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 2)

        outer.addWidget(split)

        self.cb_prod.currentIndexChanged.connect(self._update_info)
        self._update_info()

    def reload_products(self):
        self.cb_prod.blockSignals(True)
        self.cb_prod.clear()
        for pid, sku, name in self.db.product_options(True):
            self.cb_prod.addItem(f"{name} ({sku})", pid)
        self.cb_prod.blockSignals(False)

    def _update_info(self):
        pid = self.cb_prod.currentData()
        if not pid:
            self.lab_stock.setText("当前库存：—"); self.list_recent.clear(); return
        p = self.db.get_product(pid)
        if p:
            stock = float(p[6] or 0); unit = p[4] or "件"
            self.lab_stock.setText(f"当前库存：{stock:g} {unit}")
        rows = self.db.list_transactions(product_id=pid, typ="OUT")
        self.list_recent.clear()
        for r in rows[:8]:
            _id, ts, type_name, sku, name, qty, unit, price, ref, note, user, _pid = r
            self.list_recent.addItem(f"{ts} · -{qty:g}{unit} @ {price:.2f} · {ref or ''}")

    def do_out(self):
        pid = self.cb_prod.currentData()
        if not pid:
            QMessageBox.warning(self, "提示", "请选择商品")
            return
        try:
            self.db.stock_out(
                product_id=pid,
                qty=float(self.sp_qty.value()),
                unit_price=float(self.sp_price.value()),
                ref=self.ed_ref.text().strip(),
                note=self.ed_note.text().strip(),
                user="Admin"
            )
            QMessageBox.information(self, "成功", "出库完成")
            self._update_info()
            self.notify_refresh_all()
        except Exception as e:
            QMessageBox.warning(self, "失败", str(e))


# ---------------------------
# 页面：事务记录
# ---------------------------
class TransactionsPage(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        outer = QVBoxLayout(self); outer.setContentsMargins(12, 12, 12, 12); outer.setSpacing(12)

        # 过滤器
        filt_g = QGroupBox("筛选")
        f = QHBoxLayout(filt_g)
        self.dt_from = QDateEdit(); self.dt_from.setCalendarPopup(True)
        self.dt_to = QDateEdit(); self.dt_to.setCalendarPopup(True)
        today = QDate.currentDate()
        self.dt_from.setDate(today.addDays(-30))
        self.dt_to.setDate(today)
        self.cb_prod = QComboBox(); self.reload_products(include_all=True)
        self.cb_type = QComboBox(); self.cb_type.addItems(["全部", "入库", "出库"])
        btn_query = QPushButton("查询"); btn_query.clicked.connect(self.refresh)
        btn_export = QPushButton("导出 CSV"); btn_export.clicked.connect(self.export_csv)
        f.addWidget(QLabel("开始：")); f.addWidget(self.dt_from)
        f.addWidget(QLabel("结束：")); f.addWidget(self.dt_to)
        f.addWidget(QLabel("商品：")); f.addWidget(self.cb_prod)
        f.addWidget(QLabel("类型：")); f.addWidget(self.cb_type)
        f.addStretch(); f.addWidget(btn_query); f.addWidget(btn_export)

        # 表格
        self.table = QTableWidget(0, 11)
        self.table.setHorizontalHeaderLabels(["ID", "时间", "类型", "SKU", "名称", "数量", "单位", "单价", "参考号", "备注", "用户"])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)

        outer.addWidget(filt_g)
        outer.addWidget(self.table)
        self.refresh()

    def reload_products(self, include_all=False):
        self.cb_prod.clear()
        if include_all:
            self.cb_prod.addItem("全部", 0)
        for pid, sku, name in self.db.product_options(False):
            self.cb_prod.addItem(f"{name} ({sku})", pid)

    def refresh(self):
        start = self.dt_from.date().toString("yyyy-MM-dd")
        end = self.dt_to.date().toString("yyyy-MM-dd")
        pid = self.cb_prod.currentData()
        pid = None if (pid in (0, None)) else int(pid)
        typ_map = {"全部": None, "入库": "IN", "出库": "OUT"}
        typ = typ_map.get(self.cb_type.currentText(), None)

        rows = self.db.list_transactions(start, end, pid, typ)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            # row: id, ts, type_name, sku, name, qty, unit, price, ref, note, user, pid
            display = list(row[:-1])
            for c, val in enumerate(display):
                item = QTableWidgetItem(str(val))
                if c in (0, 5, 7):  # 数值靠右
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.table.setItem(r, c, item)
        self.table.setSortingEnabled(True)

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出 CSV", f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "CSV 文件 (*.csv)")
        if not path: return
        start = self.dt_from.date().toString("yyyy-MM-dd")
        end = self.dt_to.date().toString("yyyy-MM-dd")
        pid = self.cb_prod.currentData()
        pid = None if (pid in (0, None)) else int(pid)
        typ_map = {"全部": None, "入库": "IN", "出库": "OUT"}
        typ = typ_map.get(self.cb_type.currentText(), None)
        rows = self.db.list_transactions(start, end, pid, typ)
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["ID", "时间", "类型", "SKU", "名称", "数量", "单位", "单价", "参考号", "备注", "用户"])
            for r in rows:
                w.writerow(r[:-1])
        QMessageBox.information(self, "完成", f"已导出：{path}")


# ---------------------------
# 页面：设置
# ---------------------------
class SettingsPage(QWidget):
    def __init__(self, app: QApplication, toggle_theme_callback):
        super().__init__()
        self._app = app
        self._toggle = toggle_theme_callback

        layout = QVBoxLayout(self); layout.setContentsMargins(12, 12, 12, 12); layout.setSpacing(12)

        form = QFormLayout()
        self.cb_theme = QComboBox(); self.cb_theme.addItems(["深色", "浅色"]); self.cb_theme.setCurrentIndex(1)
        btn_apply = QPushButton("应用主题"); btn_apply.clicked.connect(self.apply_theme)
        form.addRow("主题：", self.cb_theme)
        form.addRow(btn_apply)

        backup_g = QGroupBox("数据库")
        h = QHBoxLayout(backup_g)
        self.lab_db = QLabel(os.path.abspath(DB_FILE))
        btn_backup = QPushButton("备份数据库…"); btn_backup.clicked.connect(self.backup_db)
        h.addWidget(QLabel("路径：")); h.addWidget(self.lab_db); h.addStretch(); h.addWidget(btn_backup)

        layout.addLayout(form)
        layout.addWidget(backup_g)
        layout.addStretch()

    def apply_theme(self):
        is_dark = self.cb_theme.currentIndex() == 0
        self._toggle(is_dark)

    def backup_db(self):
        if not os.path.exists(DB_FILE):
            QMessageBox.warning(self, "失败", "数据库不存在")
            return
        target, _ = QFileDialog.getSaveFileName(self, "另存为", f"inventory_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db", "SQLite DB (*.db)")
        if not target: return
        try:
            shutil.copyfile(DB_FILE, target)
            QMessageBox.information(self, "完成", f"已备份到：{target}")
        except Exception as e:
            QMessageBox.warning(self, "失败", str(e))


# ---------------------------
# 主窗口
# ---------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1280, 820)

        # 数据库
        self.db = Database(DB_FILE)

        # 菜单/工具条/状态栏
        self._build_menubar()
        self._build_toolbar()
        self._build_statusbar()

        # 中心区：左树 + 右页
        splitter = QSplitter(); splitter.setHandleWidth(8)

        self.left_tree = self._build_left_tree()
        splitter.addWidget(self.left_tree)

        self.pages = QStackedWidget()
        self.page_dashboard = DashboardPage(self.db)
        self.page_products = ProductsPage(self.db, on_data_changed=self.refresh_all)
        self.page_in = StockInPage(self.db, notify_refresh_all=self.refresh_all)
        self.page_out = StockOutPage(self.db, notify_refresh_all=self.refresh_all)
        self.page_tx = TransactionsPage(self.db)
        self.page_settings = SettingsPage(QApplication.instance(), self._toggle_theme)

        for p in [self.page_dashboard, self.page_products, self.page_in, self.page_out, self.page_tx, self.page_settings]:
            self.pages.addWidget(p)

        splitter.addWidget(self.pages)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 5)
        self.setCentralWidget(splitter)

        self.pages.setCurrentIndex(0)
        self.statusBar().showMessage("就绪")

    # --- UI 构建 ---
    def _build_menubar(self):
        m = self.menuBar()

        # 文件
        fmenu = m.addMenu("文件(&F)")
        act_open = QAction(self.style().standardIcon(QStyle.SP_DirOpenIcon), "导入数据(&I)…", self); act_open.setShortcut("Ctrl+I")
        act_save = QAction(self.style().standardIcon(QStyle.SP_DialogSaveButton), "导出事务(&E)…", self); act_save.setShortcut("Ctrl+E")
        act_backup = QAction("数据库备份(&B)…", self)
        act_quit = QAction(self.style().standardIcon(QStyle.SP_DialogCloseButton), "退出(&Q)", self); act_quit.setShortcut("Ctrl+Q")
        act_quit.triggered.connect(self.close)
        act_backup.triggered.connect(self._backup_via_menu)
        act_save.triggered.connect(lambda: self._export_tx_via_menu())
        fmenu.addAction(act_open)  # 预留：可扩展 CSV 导入商品
        fmenu.addAction(act_save)
        fmenu.addAction(act_backup)
        fmenu.addSeparator()
        fmenu.addAction(act_quit)

        # 编辑
        emenu = m.addMenu("编辑(&E)")
        for name, sc in [("撤销(&U)", "Ctrl+Z"), ("重做(&R)", "Ctrl+Y"), ("剪切(&T)", "Ctrl+X"),
                         ("复制(&C)", "Ctrl+C"), ("粘贴(&P)", "Ctrl+V"), ("查找(&F)…", "Ctrl+F")]:
            act = QAction(name, self); act.setShortcut(sc); emenu.addAction(act)

        # 视图
        vmenu = m.addMenu("视图(&V)")
        self.act_toggle_left = QAction("显示/隐藏左侧导航(&L)", self, checkable=True, checked=True); self.act_toggle_left.setShortcut("Ctrl+L")
        self.act_toggle_left.triggered.connect(lambda checked: self.left_tree.setVisible(checked))
        self.act_dark = QAction("深色主题(&D)", self, checkable=True, checked=True)
        self.act_dark.triggered.connect(lambda checked: self._toggle_theme(checked))
        act_expand = QAction("展开全部(&E)", self); act_expand.setShortcut("Ctrl+Shift+E"); act_expand.triggered.connect(lambda: self.left_tree.expandAll())
        act_collapse = QAction("收起全部(&C)", self); act_collapse.setShortcut("Ctrl+Shift+C"); act_collapse.triggered.connect(lambda: self.left_tree.collapseAll())
        vmenu.addAction(self.act_toggle_left); vmenu.addAction(self.act_dark); vmenu.addSeparator(); vmenu.addAction(act_expand); vmenu.addAction(act_collapse)

        # 帮助
        hmenu = m.addMenu("帮助(&H)")
        act_about = QAction("关于(&A)", self); act_about.setShortcut("F1"); act_about.triggered.connect(self._show_about)
        act_about_qt = QAction("关于 Qt", self); act_about_qt.triggered.connect(QApplication.instance().aboutQt)
        hmenu.addAction(act_about); hmenu.addAction(act_about_qt)

    def _build_toolbar(self):
        tool = QToolBar("顶部工具条", self)
        tool.setIconSize(QSize(18, 18))
        tool.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, tool)

        title = QLabel(APP_TITLE)
        f = title.font(); f.setPointSize(12); f.setBold(True); title.setFont(f)
        title.setContentsMargins(8, 0, 16, 0)
        tool.addWidget(title)

        act_refresh = QAction(self.style().standardIcon(QStyle.SP_BrowserReload), "刷新", self)
        act_refresh.setShortcut("F5")
        act_refresh.triggered.connect(self.refresh_all)
        tool.addAction(act_refresh)

        tool.addSeparator()
        self.ed_quick = QLineEdit(); self.ed_quick.setPlaceholderText("快速搜索商品（输入后回车）"); self.ed_quick.returnPressed.connect(self._quick_search)
        self.ed_quick.setFixedWidth(280)
        tool.addWidget(self.ed_quick)

        spacer = QWidget(); spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tool.addWidget(spacer)

        user_label = QLabel("用户：Admin")
        sys_label = QLabel("系统：正常")
        tool.addWidget(user_label); tool.addSeparator(); tool.addWidget(sys_label)

    def _build_statusbar(self):
        bar = QStatusBar(); self.setStatusBar(bar)
        self.lbl_user = QLabel("👤 Admin")
        self.lbl_sys = QLabel("🖥️ 正常")
        bar.addPermanentWidget(self.lbl_user)
        bar.addPermanentWidget(self.lbl_sys)

    def _build_left_tree(self):
        tree = QTreeWidget(); tree.setHeaderHidden(True); tree.setAnimated(True); tree.setIndentation(18)
        # 根
        dash = QTreeWidgetItem(["仪表板"]); dash.setIcon(0, self.style().standardIcon(QStyle.SP_ComputerIcon)); dash.setData(0, Qt.UserRole, 0)
        goods = QTreeWidgetItem(["商品管理"]); goods.setIcon(0, self.style().standardIcon(QStyle.SP_DirIcon)); goods.setData(0, Qt.UserRole, 1)
        inb = QTreeWidgetItem(["入库管理"]); inb.setIcon(0, self.style().standardIcon(QStyle.SP_ArrowUp)); inb.setData(0, Qt.UserRole, 2)
        outb = QTreeWidgetItem(["出库管理"]); outb.setIcon(0, self.style().standardIcon(QStyle.SP_ArrowDown)); outb.setData(0, Qt.UserRole, 3)
        tx = QTreeWidgetItem(["库存事务记录"]); tx.setIcon(0, self.style().standardIcon(QStyle.SP_FileDialogDetailedView)); tx.setData(0, Qt.UserRole, 4)
        settings = QTreeWidgetItem(["设置"]); settings.setIcon(0, self.style().standardIcon(QStyle.SP_FileDialogInfoView)); settings.setData(0, Qt.UserRole, 5)
        tree.addTopLevelItems([dash, goods, inb, outb, tx, settings])
        tree.expandAll()
        tree.itemClicked.connect(self._on_tree_clicked)
        tree.setMinimumWidth(220)
        return tree

    # --- 事件 ---
    def _on_tree_clicked(self, item: QTreeWidgetItem, column: int):
        idx = item.data(0, Qt.UserRole)
        if isinstance(idx, int):
            self.pages.setCurrentIndex(idx)
            self.statusBar().showMessage(f"切换到：{item.text(0)}", 1200)

    def _quick_search(self):
        kw = self.ed_quick.text().strip()
        self.pages.setCurrentIndex(1)
        self.page_products.ed_search.setText(kw)

    def _toggle_theme(self, dark: bool):
        app = QApplication.instance()
        if dark:
            apply_dark_theme(app)
            self.act_dark.setChecked(True)
        else:
            apply_light_theme(app)
            self.act_dark.setChecked(False)

    def _show_about(self):
        QMessageBox.information(self, "关于",
                                "库存管理系统 (PyQt5 + sqlite3)\n\n"
                                "• 商品管理、入库、出库、事务记录\n"
                                "• 低库存提醒、CSV 导出、数据库备份\n"
                                "• 深色/浅色主题\n")

    def _backup_via_menu(self):
        self.pages.setCurrentIndex(5)
        self.page_settings.backup_db()

    def _export_tx_via_menu(self):
        self.pages.setCurrentIndex(4)
        self.page_tx.export_csv()

    def refresh_all(self):
        # 刷新各页面数据源
        self.page_dashboard.refresh()
        self.page_products.refresh()
        self.page_in.reload_products(); self.page_in._update_info()
        self.page_out.reload_products(); self.page_out._update_info()
        self.page_tx.reload_products(include_all=True); self.page_tx.refresh()
        self.statusBar().showMessage("已刷新", 1200)


def main():
    app = QApplication(sys.argv)
    apply_dark_theme(app)  # 默认深色

    w = MainWindow()
    w.setWindowIcon(w.style().standardIcon(QStyle.SP_DesktopIcon))
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
