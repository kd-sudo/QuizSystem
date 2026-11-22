import sys
import sqlite3
from paths import get_db_path
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QLineEdit, QMessageBox, QHeaderView
)

class StudentWindow(QWidget):
    def __init__(self, student_id, student_name):
        super().__init__()
        self.student_id = student_id
        self.student_name = student_name
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f"QuizArena — Кабінет студента ({self.student_name})")
        self.setStyleSheet("""
            QWidget {
                background-color: #f4f6f9;
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #2d3436;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #ced6e0;
                border-radius: 6px;
                padding: 10px;
                font-size: 11pt;
            }
            QLineEdit:focus {
                border: 2px solid #0984e3;
            }
            QPushButton {
                background-color: #0984e3;
                color: white;
                font-weight: bold;
                padding: 10px 16px;
                border-radius: 6px;
                border: none;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #0773c5;
            }
            QPushButton#dangerBtn {
                background-color: #d63031;
            }
            QTableWidget {
                background-color: #ffffff;
                gridline-color: #dfe6e9;
                border: 1px solid #dfe6e9;
                border-radius: 6px;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)

        top_bar = QHBoxLayout()
        welcome_lbl = QLabel(f"🎓 Студент: <b>{self.student_name}</b>")
        welcome_lbl.setStyleSheet("font-size: 13pt;")

        btn_logout = QPushButton("Вийти")
        btn_logout.setObjectName("dangerBtn")
        btn_logout.clicked.connect(self.logout)

        top_bar.addWidget(welcome_lbl)
        top_bar.addStretch()
        top_bar.addWidget(btn_logout)
        main_layout.addLayout(top_bar)

        pin_layout = QHBoxLayout()
        pin_label = QLabel("🔑 Швидкий вхід за PIN-кодом:")
        pin_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        
        self.input_pin = QLineEdit()
        self.input_pin.setPlaceholderText("Введіть 6-значний PIN (напр. 482910)")
        self.input_pin.setFixedWidth(250)
        self.input_pin.returnPressed.connect(self.join_by_pin)
        
        btn_join_pin = QPushButton("Підключитися до тесту")
        btn_join_pin.setStyleSheet("background-color: #00b894;")
        btn_join_pin.clicked.connect(self.join_by_pin)

        pin_layout.addWidget(pin_label)
        pin_layout.addWidget(self.input_pin)
        pin_layout.addWidget(btn_join_pin)
        pin_layout.addStretch()
        main_layout.addLayout(pin_layout)

        lbl_tests = QLabel("📋 Доступні активні тести («В прямому ефірі»):")
        lbl_tests.setStyleSheet("font-weight: bold; font-size: 11pt; margin-top: 10px;")
        main_layout.addWidget(lbl_tests)

        self.tests_table = QTableWidget()
        self.tests_table.setColumnCount(5)
        self.tests_table.setHorizontalHeaderLabels([
            "ID", "Назва тесту", "Предмет", "Час на питання", "PIN-код"
        ])
        self.tests_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        main_layout.addWidget(self.tests_table)

        btn_start = QPushButton("🚀 Розпочати обраний тест")
        btn_start.setStyleSheet("background-color: #0984e3; font-size: 12pt; padding: 12px;")
        btn_start.clicked.connect(self.start_selected_test)
        main_layout.addWidget(btn_start)

        self.load_active_tests()

    def load_active_tests(self):
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, subject, time_limit, access_code FROM tests WHERE is_active = 1")
        tests = cursor.fetchall()
        conn.close()

        self.tests_table.setRowCount(len(tests))
        for row_idx, test in enumerate(tests):
            for col_idx, val in enumerate(test):
                if col_idx == 3:
                    val = f"{val} сек"
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tests_table.setItem(row_idx, col_idx, item)

    def check_and_run_test(self, test_id):
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT max_attempts FROM tests WHERE id = ?", (test_id,))
        res = cursor.fetchone()
        if not res:
            conn.close()
            return
        max_attempts = res[0]

        cursor.execute("SELECT COUNT(*) FROM attempts WHERE student_id = ? AND test_id = ?", (self.student_id, test_id))
        attempts_made = cursor.fetchone()[0]
        conn.close()

        if attempts_made >= max_attempts:
            QMessageBox.warning(self, "Ліміт вичерпано", f"Ви вже використували всі дозволені спроби ({attempts_made}/{max_attempts}) для цього тесту.")
            return

        from test_run_window import TestRunWindow
        self.test_win = TestRunWindow(student_id=self.student_id, test_id=test_id)
        self.test_win.showMaximized()
        self.close()

    def start_selected_test(self):
        selected = self.tests_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Увага", "Оберіть тест зі списку.")
            return
        test_id = int(self.tests_table.item(selected, 0).text())
        self.check_and_run_test(test_id)

    def join_by_pin(self):
        pin = self.input_pin.text().strip()
        if not pin:
            QMessageBox.warning(self, "Увага", "Введіть PIN-код.")
            return

        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT id, is_active FROM tests WHERE access_code = ?", (pin,))
        test = cursor.fetchone()
        conn.close()

        if not test:
            QMessageBox.critical(self, "Помилка", "Тест із таким PIN-кодом не знайдено.")
            return
        
        test_id, is_active = test
        if is_active == 0:
            QMessageBox.warning(self, "Закрито", "Цей тест наразі не в ефірі (закритий викладачем).")
            return

        self.check_and_run_test(test_id)

    def logout(self):
        from auth import AuthWindow
        self.auth_win = AuthWindow()
        self.auth_win.showMaximized()
        self.close()