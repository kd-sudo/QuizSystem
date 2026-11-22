import sys
import sqlite3
import hashlib
from paths import get_db_path
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox, QComboBox, QFrame
)
from database import init_db

TEXTS = {
    'uk': {
        'window_title': "QuizArena — Освітня платформа тестування",
        'subtitle_login': "Вхід до освітнього середовища",
        'subtitle_reg': "Реєстрація нового користувача",
        'fullname': "Прізвище та ім'я:",
        'fullname_placeholder': "Наприклад: Іваненко Олександр",
        'username': "Логін:",
        'username_placeholder': "Введіть логін",
        'password': "Пароль:",
        'password_placeholder': "Введіть пароль",
        'confirm_password': "Підтвердіть пароль:",
        'confirm_password_placeholder': "Повторіть пароль",
        'role': "Оберіть роль:",
        'role_student': "Студент / Учень",
        'role_teacher': "Викладач / Вчитель",
        'group': "Група / Клас:",
        'group_placeholder': "Наприклад: ПЗ-11",
        'btn_login': "Увійти в систему",
        'btn_reg': "Створити обліковий запис",
        'toggle_to_reg': "Немає акаунту? Зареєструватися",
        'toggle_to_login': "Вже зареєстровані? Увійти",
        'error_empty': "Будь ласка, заповніть усі поля.",
        'error_name': "Введіть прізвище та ім'я.",
        'error_pass_mismatch': "Паролі не співпадають!",
        'success_reg': "Реєстрація успішна! Тепер ви можете увійти.",
        'error_exists': "Користувач із таким логіном вже існує.",
        'error_auth': "Невірний логін або пароль."
    },
    'en': {
        'window_title': "QuizArena — Educational Testing Platform",
        'subtitle_login': "Sign in to the educational environment",
        'subtitle_reg': "Create a new account",
        'fullname': "Full Name:",
        'fullname_placeholder': "e.g., John Smith",
        'username': "Username:",
        'username_placeholder': "Enter username",
        'password': "Password:",
        'password_placeholder': "Enter password",
        'confirm_password': "Confirm Password:",
        'confirm_password_placeholder': "Repeat password",
        'role': "Select Role:",
        'role_student': "Student / Pupil",
        'role_teacher': "Teacher / Instructor",
        'group': "Group / Class:",
        'group_placeholder': "e.g., CS-11",
        'btn_login': "Sign In",
        'btn_reg': "Create Account",
        'toggle_to_reg': "Don't have an account? Sign up",
        'toggle_to_login': "Already have an account? Sign in",
        'error_empty': "Please fill in all fields.",
        'error_name': "Please enter your full name.",
        'error_pass_mismatch': "Passwords do not match!",
        'success_reg': "Registration successful! You can now sign in.",
        'error_exists': "A user with this username already exists.",
        'error_auth': "Invalid username or password."
    }
}

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

class AuthWindow(QWidget):
    def __init__(self):
        super().__init__()
        init_db()
        self.is_register_mode = False
        self.current_lang = 'uk'
        self.is_dark_theme = False
        self.initUI()

    def initUI(self):
        t = TEXTS[self.current_lang]
        self.setWindowTitle(t['window_title'])
        self.apply_theme()

        # Головний макет вікна
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Верхня панель з кнопками мови та теми
        top_controls_layout = QHBoxLayout()
        self.btn_lang = QPushButton("🇺🇦 UA / EN")
        self.btn_lang.setFixedWidth(100)
        self.btn_lang.clicked.connect(self.toggle_language)

        self.btn_theme = QPushButton("🌙 Тема")
        self.btn_theme.setFixedWidth(100)
        self.btn_theme.clicked.connect(self.toggle_theme)

        top_controls_layout.addWidget(self.btn_lang)
        top_controls_layout.addWidget(self.btn_theme)
        top_controls_layout.addStretch()
        main_layout.addLayout(top_controls_layout)

        # Вертикальні пружини зверху і знизу для центрування картки по вертикалі
        main_layout.addStretch()

        # Горизонтальний контейнер для центрування картки по горизонталі
        h_layout = QHBoxLayout()
        h_layout.addStretch()

        # Картка авторизації
        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(430)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(35, 30, 35, 30)
        card_layout.setSpacing(10)

        self.label_logo = QLabel("🎓 QuizArena")
        self.label_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_logo.setStyleSheet("font-size: 22pt; font-weight: bold; color: #0984e3;")
        card_layout.addWidget(self.label_logo)

        self.label_subtitle = QLabel(t['subtitle_login'])
        self.label_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_subtitle.setStyleSheet("font-size: 11pt; color: #636e72; margin-bottom: 4px;")
        card_layout.addWidget(self.label_subtitle)

        self.label_fullname = QLabel(t['fullname'])
        self.input_fullname = QLineEdit()
        self.input_fullname.setPlaceholderText(t['fullname_placeholder'])
        card_layout.addWidget(self.label_fullname)
        card_layout.addWidget(self.input_fullname)

        self.label_group = QLabel(t['group'])
        self.input_group = QLineEdit()
        self.input_group.setPlaceholderText(t['group_placeholder'])
        card_layout.addWidget(self.label_group)
        card_layout.addWidget(self.input_group)

        self.lbl_user = QLabel(t['username'])
        self.input_username = QLineEdit()
        self.input_username.setPlaceholderText(t['username_placeholder'])
        card_layout.addWidget(self.lbl_user)
        card_layout.addWidget(self.input_username)

        self.lbl_pass = QLabel(t['password'])
        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText(t['password_placeholder'])
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        card_layout.addWidget(self.lbl_pass)
        card_layout.addWidget(self.input_password)

        self.label_confirm_pass = QLabel(t['confirm_password'])
        self.input_confirm_password = QLineEdit()
        self.input_confirm_password.setPlaceholderText(t['confirm_password_placeholder'])
        self.input_confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_confirm_password.returnPressed.connect(self.handle_action)
        card_layout.addWidget(self.label_confirm_pass)
        card_layout.addWidget(self.input_confirm_password)

        self.label_role = QLabel(t['role'])
        self.combo_role = QComboBox()
        self.combo_role.addItem(t['role_student'], "student")
        self.combo_role.addItem(t['role_teacher'], "teacher")
        card_layout.addWidget(self.label_role)
        card_layout.addWidget(self.combo_role)

        self.btn_submit = QPushButton(t['btn_login'])
        self.btn_submit.setObjectName("primaryBtn")
        self.btn_submit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_submit.clicked.connect(self.handle_action)
        card_layout.addWidget(self.btn_submit)

        self.btn_toggle = QPushButton(t['toggle_to_reg'])
        self.btn_toggle.setObjectName("linkBtn")
        self.btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle.clicked.connect(self.toggle_mode)
        card_layout.addWidget(self.btn_toggle)

        h_layout.addWidget(card)
        h_layout.addStretch()
        
        main_layout.addLayout(h_layout)
        main_layout.addStretch()
        
        self.update_form_visibility()

    def apply_theme(self):
        if self.is_dark_theme:
            self.setStyleSheet("""
                QWidget {
                    background-color: #1e1e1e;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    color: #f5f6fa;
                }
                QFrame#card {
                    background-color: #2d2d2d;
                    border: 1px solid #3f3f3f;
                    border-radius: 16px;
                }
                QLineEdit, QComboBox {
                    background-color: #383838;
                    border: 1px solid #555555;
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-size: 10pt;
                    color: #ffffff;
                }
                QLineEdit:focus, QComboBox:focus {
                    border: 2px solid #0984e3;
                }
                QPushButton#primaryBtn {
                    background-color: #0984e3;
                    color: white;
                    font-size: 10pt;
                    font-weight: bold;
                    padding: 10px;
                    border-radius: 8px;
                    border: none;
                }
                QPushButton#primaryBtn:hover {
                    background-color: #0773c5;
                }
                QPushButton#linkBtn {
                    background: transparent;
                    color: #74b9ff;
                    font-size: 9pt;
                    font-weight: bold;
                    border: none;
                    text-decoration: underline;
                }
                QPushButton {
                    background-color: #383838;
                    color: #f5f6fa;
                    border: 1px solid #555555;
                    border-radius: 6px;
                    padding: 6px;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: #f4f6f9;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    color: #2d3436;
                }
                QFrame#card {
                    background-color: #ffffff;
                    border: 1px solid #dfe6e9;
                    border-radius: 16px;
                }
                QLineEdit, QComboBox {
                    background-color: #f8f9fa;
                    border: 1px solid #ced6e0;
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-size: 10pt;
                    color: #2d3436;
                }
                QLineEdit:focus, QComboBox:focus {
                    border: 2px solid #0984e3;
                    background-color: #ffffff;
                }
                QPushButton#primaryBtn {
                    background-color: #0984e3;
                    color: white;
                    font-size: 10pt;
                    font-weight: bold;
                    padding: 10px;
                    border-radius: 8px;
                    border: none;
                }
                QPushButton#primaryBtn:hover {
                    background-color: #0773c5;
                }
                QPushButton#linkBtn {
                    background: transparent;
                    color: #0984e3;
                    font-size: 9pt;
                    font-weight: bold;
                    border: none;
                    text-decoration: underline;
                }
                QPushButton {
                    background-color: #ffffff;
                    color: #2d3436;
                    border: 1px solid #ced6e0;
                    border-radius: 6px;
                    padding: 6px;
                }
            """)

    def toggle_language(self):
        self.current_lang = 'en' if self.current_lang == 'uk' else 'uk'
        self.update_ui_texts()

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        self.apply_theme()

    def update_ui_texts(self):
        t = TEXTS[self.current_lang]
        self.setWindowTitle(t['window_title'])
        self.label_subtitle.setText(t['subtitle_reg'] if self.is_register_mode else t['subtitle_login'])
        self.label_fullname.setText(t['fullname'])
        self.input_fullname.setPlaceholderText(t['fullname_placeholder'])
        self.label_group.setText(t['group'])
        self.input_group.setPlaceholderText(t['group_placeholder'])
        self.lbl_user.setText(t['username'])
        self.input_username.setPlaceholderText(t['username_placeholder'])
        self.lbl_pass.setText(t['password'])
        self.input_password.setPlaceholderText(t['password_placeholder'])
        self.label_confirm_pass.setText(t['confirm_password'])
        self.input_confirm_password.setPlaceholderText(t['confirm_password_placeholder'])
        self.label_role.setText(t['role'])
        
        self.combo_role.setItemText(0, t['role_student'])
        self.combo_role.setItemText(1, t['role_teacher'])

        self.btn_submit.setText(t['btn_reg'] if self.is_register_mode else t['btn_login'])
        self.btn_toggle.setText(t['toggle_to_login'] if self.is_register_mode else t['toggle_to_reg'])

    def update_form_visibility(self):
        is_reg = self.is_register_mode
        self.label_fullname.setVisible(is_reg)
        self.input_fullname.setVisible(is_reg)
        self.label_group.setVisible(is_reg)
        self.input_group.setVisible(is_reg)
        self.label_confirm_pass.setVisible(is_reg)
        self.input_confirm_password.setVisible(is_reg)
        self.label_role.setVisible(is_reg)
        self.combo_role.setVisible(is_reg)
        self.update_ui_texts()

    def toggle_mode(self):
        self.is_register_mode = not self.is_register_mode
        self.update_form_visibility()

    def handle_action(self):
        t = TEXTS[self.current_lang]
        username = self.input_username.text().strip()
        password = self.input_password.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Увага", t['error_empty'])
            return

        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()

        if self.is_register_mode:
            full_name = self.input_fullname.text().strip()
            group_name = self.input_group.text().strip() or "ПЗ-11"
            confirm_password = self.input_confirm_password.text().strip()
            role = self.combo_role.currentData()

            if not full_name:
                QMessageBox.warning(self, "Увага", t['error_name'])
                conn.close()
                return

            if password != confirm_password:
                QMessageBox.warning(self, "Помилка", t['error_pass_mismatch'])
                conn.close()
                return

            try:
                cursor.execute(
                    "INSERT INTO users (username, password, full_name, role, group_name) VALUES (?, ?, ?, ?, ?)",
                    (username, hash_password(password), full_name, role, group_name)
                )
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Успіх", t['success_reg'])
                
                self.is_register_mode = False
                self.input_fullname.clear()
                self.input_group.clear()
                self.input_password.clear()
                self.input_confirm_password.clear()
                self.update_form_visibility()
                return
            except sqlite3.IntegrityError:
                conn.close()
                QMessageBox.warning(self, "Помилка", t['error_exists'])
        else:
            cursor.execute(
                "SELECT id, full_name, role FROM users WHERE username = ? AND password = ?",
                (username, hash_password(password))
            )
            user = cursor.fetchone()
            conn.close()

            if user:
                user_id, full_name, role = user
                try:
                    self.close()
                    app_instance = QApplication.instance()
                    if role == 'teacher':
                        from teacher_window import TeacherWindow
                        app_instance.main_window = TeacherWindow(teacher_id=user_id, teacher_name=full_name)
                        app_instance.main_window.showMaximized()
                    else:
                        from student_window import StudentWindow
                        app_instance.main_window = StudentWindow(student_id=user_id, student_name=full_name)
                        app_instance.main_window.showMaximized()
                except Exception as e:
                    QMessageBox.critical(self, "Помилка коду", f"Не вдалося відкрити вікно:\n{str(e)}")
            else:
                QMessageBox.critical(self, "Помилка", t['error_auth'])