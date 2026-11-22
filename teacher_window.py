import sys
import sqlite3
import csv
from paths import get_db_path
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QTabWidget, QLineEdit,
    QTextEdit, QMessageBox, QComboBox, QSpinBox, QFileDialog, QHeaderView, QFrame, QScrollArea
)

class QuestionWidget(QFrame):
    def __init__(self, index, delete_callback):
        super().__init__()
        self.index = index
        self.delete_callback = delete_callback
        self.setObjectName("questionCard")
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        top_row = QHBoxLayout()
        self.lbl_title = QLabel(f"<b>Питання #{self.index}</b>")
        self.lbl_title.setStyleSheet("color: #0984e3; font-size: 11pt;")
        top_row.addWidget(self.lbl_title)
        top_row.addStretch()
        
        self.btn_delete = QPushButton("🗑 Видалити питання")
        self.btn_delete.setObjectName("dangerBtn")
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.clicked.connect(lambda: self.delete_callback(self))
        top_row.addWidget(self.btn_delete)
        
        layout.addLayout(top_row)

        self.input_question = QLineEdit()
        self.input_question.setPlaceholderText("Введіть текст запитання...")
        layout.addWidget(self.input_question)

        settings_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel("Тип:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Один варіант", "Кілька варіантів"])
        settings_layout.addWidget(self.type_combo)

        settings_layout.addWidget(QLabel("Кількість варіантів:"))
        self.combo_count = QComboBox()
        self.combo_count.addItems(["2", "3", "4", "5", "6"])
        self.combo_count.setCurrentIndex(2)
        self.combo_count.currentIndexChanged.connect(self.update_variant_fields)
        settings_layout.addWidget(self.combo_count)
        settings_layout.addStretch()

        layout.addLayout(settings_layout)

        self.variants_layout = QVBoxLayout()
        layout.addLayout(self.variants_layout)

        correct_layout = QHBoxLayout()
        correct_layout.addWidget(QLabel("Номер правильної відповіді (напр. 1 або 1,2):"))
        self.input_correct = QLineEdit()
        self.input_correct.setFixedWidth(120)
        self.input_correct.setPlaceholderText("1")
        correct_layout.addWidget(self.input_correct)
        correct_layout.addStretch()
        layout.addLayout(correct_layout)

        self.variant_inputs = []
        self.update_variant_fields()

    def update_variant_fields(self):
        for i in range(self.variants_layout.count()):
            item = self.variants_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        
        self.variant_inputs = []
        count = int(self.combo_count.currentText())

        for i in range(count):
            row_layout = QHBoxLayout()
            lbl = QLabel(f"Варіант {i+1}:")
            lbl.setFixedWidth(70)
            
            inp = QLineEdit()
            inp.setPlaceholderText(f"Введіть текст варіанту {i+1}")
            
            row_layout.addWidget(lbl)
            row_layout.addWidget(inp)
            
            container = QWidget()
            container.setLayout(row_layout)
            self.variants_layout.addWidget(container)
            self.variant_inputs.append(inp)


class TeacherWindow(QWidget):
    def __init__(self, teacher_id, teacher_name):
        super().__init__()
        self.teacher_id = teacher_id
        self.teacher_name = teacher_name
        self.question_widgets = []
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f"QuizArena — Кабінет викладача ({self.teacher_name})")
        self.setStyleSheet("""
            QWidget {
                background-color: #f4f6f9;
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #2d3436;
            }
            QTabWidget::pane {
                border: 1px solid #dfe6e9;
                background: #ffffff;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #dfe6e9;
                color: #2d3436;
                padding: 10px 20px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #0984e3;
                color: white;
            }
            QLineEdit, QComboBox, QSpinBox, QTextEdit {
                background-color: #ffffff;
                border: 1px solid #ced6e0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 10pt;
            }
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
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
            QPushButton#dangerBtn:hover {
                background-color: #c0392b;
            }
            QFrame#questionCard {
                background-color: #ffffff;
                border: 1px solid #dfe6e9;
                border-radius: 8px;
                margin-bottom: 10px;
            }
            QTableWidget {
                background-color: #ffffff;
                gridline-color: #dfe6e9;
                border: 1px solid #dfe6e9;
                border-radius: 6px;
            }
        """)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        top_bar = QHBoxLayout()
        welcome_lbl = QLabel(f"👨‍🏫 Викладач: <b>{self.teacher_name}</b>")
        welcome_lbl.setStyleSheet("font-size: 13pt; color: #2d3436;")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Пошук тестів за назвою або PIN...")
        self.search_input.setFixedWidth(300)
        self.search_input.textChanged.connect(self.load_tests)
        
        btn_logout = QPushButton("Вийти з акаунту")
        btn_logout.setObjectName("dangerBtn")
        btn_logout.clicked.connect(self.logout)
        
        top_bar.addWidget(welcome_lbl)
        top_bar.addStretch()
        top_bar.addWidget(self.search_input)
        top_bar.addWidget(btn_logout)
        main_layout.addLayout(top_bar)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        self.tab_tests = QWidget()
        self.tab_create = QWidget()
        self.tab_results = QWidget()
        
        self.tabs.addTab(self.tab_tests, "📋 Мої тести та статус")
        self.tabs.addTab(self.tab_create, "➕ Створити новий тест")
        self.tabs.addTab(self.tab_results, "📊 Журнал результатів та груп")
        
        self.init_tests_tab()
        self.init_create_tab()
        self.init_results_tab()

    def init_tests_tab(self):
        layout = QVBoxLayout(self.tab_tests)
        self.tests_table = QTableWidget()
        self.tests_table.setColumnCount(7)
        self.tests_table.setHorizontalHeaderLabels([
            "ID", "Назва тесту", "Предмет", "PIN-код", "Час (хв)", "Спроби", "Статус (В ефірі)"
        ])
        self.tests_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tests_table)
        
        btn_layout = QHBoxLayout()
        self.btn_toggle_status = QPushButton("🔄 Змінити статус")
        self.btn_toggle_status.clicked.connect(self.toggle_test_status)
        
        self.btn_delete_test = QPushButton("🗑 Видалити тест")
        self.btn_delete_test.setObjectName("dangerBtn")
        self.btn_delete_test.clicked.connect(self.delete_test)

        self.btn_preview = QPushButton("▶️ Тестовий перегляд")
        self.btn_preview.clicked.connect(self.preview_test)
        
        btn_layout.addWidget(self.btn_toggle_status)
        btn_layout.addWidget(self.btn_delete_test)
        btn_layout.addWidget(self.btn_preview)
        
        layout.addLayout(btn_layout)
        self.load_tests()

    def load_tests(self):
        query_text = self.search_input.text().strip()
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        if query_text:
            cursor.execute("""
                SELECT id, title, subject, access_code, time_limit, max_attempts, is_active 
                FROM tests WHERE teacher_id = ? AND (title LIKE ? OR access_code LIKE ?)
            """, (self.teacher_id, f"%{query_text}%", f"%{query_text}%"))
        else:
            cursor.execute("""
                SELECT id, title, subject, access_code, time_limit, max_attempts, is_active 
                FROM tests WHERE teacher_id = ?
            """, (self.teacher_id,))
            
        tests = cursor.fetchall()
        conn.close()
        self.tests_table.setRowCount(len(tests))
        for row_idx, test in enumerate(tests):
            for col_idx, val in enumerate(test):
                if col_idx == 6:
                    val = "🟢 Активний (В ефірі)" if val == 1 else "🔴 Закритий"
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tests_table.setItem(row_idx, col_idx, item)

    def toggle_test_status(self):
        selected = self.tests_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Увага", "Оберіть тест у таблиці.")
            return
        test_id = int(self.tests_table.item(selected, 0).text())
        
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT is_active FROM tests WHERE id = ?", (test_id,))
        current_status = cursor.fetchone()[0]
        new_status = 0 if current_status == 1 else 1
        
        cursor.execute("UPDATE tests SET is_active = ? WHERE id = ?", (new_status, test_id))
        conn.commit()
        conn.close()
        self.load_tests()

    def delete_test(self):
        selected = self.tests_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Увага", "Оберіть тест для видалення в таблиці.")
            return
        test_id = int(self.tests_table.item(selected, 0).text())
        test_title = self.tests_table.item(selected, 1).text()

        confirm = QMessageBox.question(
            self, "Підтвердження",
            f"Ви дійсно хочете видалити тест «{test_title}»?\nУсі пов'язані питання та результати також будуть видалені!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tests WHERE id = ?", (test_id,))
            conn.commit()
            conn.close()
            self.load_tests()
            self.load_filter_options()
            QMessageBox.information(self, "Успіх", "Тест успішно видалено.")

    def preview_test(self):
        selected = self.tests_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Увага", "Оберіть тест для перегляду.")
            return
        test_id = int(self.tests_table.item(selected, 0).text())
        from test_run_window import TestRunWindow
        self.preview_win = TestRunWindow(student_id=self.teacher_id, test_id=test_id, is_preview=True)
        self.preview_win.showMaximized()

    def init_create_tab(self):
        layout = QVBoxLayout(self.tab_create)
        form_layout = QHBoxLayout()
        
        left_box = QVBoxLayout()
        left_box.addWidget(QLabel("<b>Назва тесту:</b>"))
        self.input_title = QLineEdit()
        left_box.addWidget(self.input_title)
        
        left_box.addWidget(QLabel("<b>Предмет / Дисципліна (тег):</b>"))
        self.input_subject = QComboBox()
        self.input_subject.addItems(["Конституційне право", "Історія України", "Інформатика", "Іноземна мова", "Загальний"])
        self.input_subject.setEditable(True)
        left_box.addWidget(self.input_subject)
        
        left_box.addWidget(QLabel("<b>Ліміт часу на питання (секунд):</b>"))
        self.spin_time = QSpinBox()
        self.spin_time.setRange(10, 120)
        self.spin_time.setValue(25)
        left_box.addWidget(self.spin_time)
        
        left_box.addWidget(QLabel("<b>Максимальна кількість спроб:</b>"))
        self.spin_attempts = QSpinBox()
        self.spin_attempts.setRange(1, 10)
        self.spin_attempts.setValue(1)
        left_box.addWidget(self.spin_attempts)
        
        left_box.addWidget(QLabel("<b>Опис тесту:</b>"))
        self.input_desc = QTextEdit()
        self.input_desc.setMaximumHeight(100)
        left_box.addWidget(self.input_desc)
        left_box.addStretch()
        form_layout.addLayout(left_box, 1)
        
        right_box = QVBoxLayout()
        right_box.addWidget(QLabel("<b>Конструктор питань:</b>"))
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.question_container = QVBoxLayout(self.scroll_content)
        self.question_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)
        right_box.addWidget(self.scroll_area)
        
        btn_add_q = QPushButton("➕ Додати питання до тесту")
        btn_add_q.clicked.connect(self.add_question_field)
        right_box.addWidget(btn_add_q)
        
        form_layout.addLayout(right_box, 2)
        layout.addLayout(form_layout)
        
        btn_save_test = QPushButton("💾 Зберегти тест у систему")
        btn_save_test.setStyleSheet("background-color: #00b894; font-size: 11pt; padding: 12px;")
        btn_save_test.clicked.connect(self.save_test)
        layout.addWidget(btn_save_test)

        self.add_question_field()

    def add_question_field(self):
        index = len(self.question_widgets) + 1
        q_widget = QuestionWidget(index, self.delete_question_widget)
        self.question_widgets.append(q_widget)
        self.question_container.addWidget(q_widget)

    def delete_question_widget(self, widget):
        self.question_container.removeWidget(widget)
        widget.deleteLater()
        self.question_widgets.remove(widget)
        for idx, qw in enumerate(self.question_widgets, start=1):
            qw.index = idx
            qw.lbl_title.setText(f"<b>Питання #{idx}</b>")

    def save_test(self):
        title = self.input_title.text().strip()
        subject = self.input_subject.currentText().strip()
        desc = self.input_desc.toPlainText().strip()
        time_limit = self.spin_time.value()
        max_attempts = self.spin_attempts.value()
        
        if not title:
            QMessageBox.warning(self, "Помилка", "Введіть назву тесту.")
            return

        if not self.question_widgets:
            QMessageBox.warning(self, "Помилка", "Додайте хоча б одне питання до тесту.")
            return

        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        from database import generate_unique_pin
        access_code = generate_unique_pin(cursor)
        
        cursor.execute("""
            INSERT INTO tests (teacher_id, title, subject, description, access_code, time_limit, max_attempts, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (self.teacher_id, title, subject, desc, access_code, time_limit, max_attempts))
        test_id = cursor.lastrowid

        saved_questions = 0
        for qw in self.question_widgets:
            q_text = qw.input_question.text().strip()
            if not q_text:
                continue
            
            q_type = 'single' if qw.type_combo.currentIndex() == 0 else 'multiple'
            cursor.execute("INSERT INTO questions (test_id, content, question_type) VALUES (?, ?, ?)", (test_id, q_text, q_type))
            q_id = cursor.lastrowid

            variants = [inp.text().strip() for inp in qw.variant_inputs if inp.text().strip()]
            correct_raw = qw.input_correct.text().strip()

            correct_indices = []
            try:
                correct_indices = [int(x.strip()) - 1 for x in correct_raw.split(',') if x.strip().isdigit()]
            except:
                correct_indices = [0]

            for idx, ans_text in enumerate(variants):
                is_correct = 1 if idx in correct_indices else 0
                cursor.execute("INSERT INTO answers (question_id, content, is_correct) VALUES (?, ?, ?)", (q_id, ans_text, is_correct))
            
            saved_questions += 1

        conn.commit()
        conn.close()

        if saved_questions == 0:
            QMessageBox.warning(self, "Увага", "Тест збережено, але жодне питання не містить тексту!")
        else:
            QMessageBox.information(self, "Успіх!", f"Тест успішно створено!\nPIN-код доступу: #{access_code}")
            self.input_title.clear()
            self.input_desc.clear()
            for qw in list(self.question_widgets):
                self.delete_question_widget(qw)
            self.add_question_field()
            self.load_tests()
            self.load_filter_options()
            self.tabs.setCurrentIndex(0)

    def init_results_tab(self):
        layout = QVBoxLayout(self.tab_results)
        
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("<b>Фільтр за групою/класом:</b>"))
        self.combo_group_filter = QComboBox()
        self.combo_group_filter.addItem("Усі групи")
        self.combo_group_filter.currentIndexChanged.connect(self.load_results)
        filter_layout.addWidget(self.combo_group_filter)
        
        filter_layout.addWidget(QLabel("<b>Фільтр за предметом:</b>"))
        self.combo_subject_filter = QComboBox()
        self.combo_subject_filter.addItem("Усі предмети")
        self.combo_subject_filter.currentIndexChanged.connect(self.load_results)
        filter_layout.addWidget(self.combo_subject_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels([
            "Студент", "Група", "Тест", "Предмет", "Бали", "Оцінка (12)", "Фокус втрачено", "Дата"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.results_table)

        btn_export = QPushButton("📥 Експортувати відомість у CSV")
        btn_export.setStyleSheet("background-color: #0984e3; font-weight: bold; padding: 10px;")
        btn_export.clicked.connect(self.export_to_csv)
        layout.addWidget(btn_export)

        self.load_filter_options()
        self.load_results()

    def load_filter_options(self):
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT group_name FROM users WHERE role = 'student'")
        groups = cursor.fetchall()
        self.combo_group_filter.clear()
        self.combo_group_filter.addItem("Усі групи")
        for g in groups:
            if g[0]:
                self.combo_group_filter.addItem(g[0])

        cursor.execute("SELECT DISTINCT subject FROM tests WHERE teacher_id = ?", (self.teacher_id,))
        subjects = cursor.fetchall()
        self.combo_subject_filter.clear()
        self.combo_subject_filter.addItem("Усі предмети")
        for s in subjects:
            if s[0]:
                self.combo_subject_filter.addItem(s[0])
        conn.close()

    def load_results(self):
        selected_group = self.combo_group_filter.currentText()
        selected_subject = self.combo_subject_filter.currentText()
        
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        query = """
            SELECT u.full_name, u.group_name, t.title, t.subject, a.score, a.max_score, a.focus_lost_count, a.attempt_date
            FROM attempts a
            JOIN users u ON a.student_id = u.id
            JOIN tests t ON a.test_id = t.id
            WHERE t.teacher_id = ?
        """
        params = [self.teacher_id]
        if selected_group and selected_group != "Усі групи":
            query += " AND u.group_name = ?"
            params.append(selected_group)
        if selected_subject and selected_subject != "Усі предмети":
            query += " AND t.subject = ?"
            params.append(selected_subject)
        
        query += " ORDER BY a.attempt_date DESC"
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()

        self.results_table.setRowCount(len(results))
        for row_idx, row_data in enumerate(results):
            score, max_score = row_data[4], row_data[5]
            grade_12 = round((score / max_score) * 12) if max_score > 0 else 0
            
            display_row = [
                row_data[0], row_data[1], row_data[2], row_data[3],
                f"{score}/{max_score}", f"{grade_12} / 12", f"{row_data[6]} раз.", row_data[7]
            ]
            
            for col_idx, val in enumerate(display_row):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.results_table.setItem(row_idx, col_idx, item)

    @staticmethod
    def _format_csv_cell(value: str) -> str:
        text = (value or "").strip()
        if not text:
            return ""
        # Захист від автоперетворення Excel у дати (напр. 0/12 -> 08.Гру) та експоненту (1E+14)
        if ("/" in text or "-" in text) or (text.replace(" ", "").isdigit() and len(text.replace(" ", "")) >= 10):
            return f'="{text}"'
        return text

    def export_to_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Зберегти відомість", "quiz_results.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            col_count = self.results_table.columnCount()
            headers = [
                self.results_table.horizontalHeaderItem(c).text()
                if self.results_table.horizontalHeaderItem(c) is not None
                else f"Стовпець {c + 1}"
                for c in range(col_count)
            ]

            with open(path, mode='w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file, delimiter=';')
                writer.writerow(headers)

                for r in range(self.results_table.rowCount()):
                    row_data = []
                    for c in range(col_count):
                        item = self.results_table.item(r, c)
                        cell_text = item.text() if item is not None else ""
                        row_data.append(self._format_csv_cell(cell_text))
                    writer.writerow(row_data)

            QMessageBox.information(self, "Успіх", "Відомість успішно експортовано!")
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося зберегти файл: {e}")

    def logout(self):
        from auth import AuthWindow
        self.auth_win = AuthWindow()
        self.auth_win.showMaximized()
        self.close()