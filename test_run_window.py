import sys
import sqlite3
import time
from paths import get_db_path
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QMessageBox, QFrame, QDialog
)

def format_long_text(text, max_len=22):
    """Розбиває довгі слова без пробірів, щоб текст завжди гарно обгортався"""
    if not text:
        return ""
    words = text.split()
    new_words = []
    for word in words:
        if len(word) > max_len:
            chunks = [word[i:i+max_len] for i in range(0, len(word), max_len)]
            new_words.append(" ".join(chunks))
        else:
            new_words.append(word)
    return " ".join(new_words)


class ClickableTile(QFrame):
    """Кастомна клікабельна плитка відповіді на базі QFrame з ідеальним багаторядковим перенесенням тексту"""
    clicked = pyqtSignal()

    def __init__(self, bg_color, symbol, text):
        super().__init__()
        self.bg_color = bg_color
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 12px;
            }}
            QFrame:hover {{
                border: 2px solid #ffffff;
            }}
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        self.lbl_symbol = QLabel(symbol)
        self.lbl_symbol.setStyleSheet("font-size: 16pt; font-weight: bold; color: white; background: transparent;")
        self.lbl_symbol.setFixedWidth(30)
        self.lbl_symbol.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Використовуємо QLabel з обгортанням, який стовідсотково переносить будь-який текст
        formatted = format_long_text(text, max_len=20)
        self.lbl_text = QLabel(formatted)
        self.lbl_text.setStyleSheet("font-size: 12pt; font-weight: bold; color: white; background: transparent;")
        self.lbl_text.setWordWrap(True)
        
        layout.addWidget(self.lbl_symbol)
        layout.addWidget(self.lbl_text, 1)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def set_active(self, enabled):
        self.setEnabled(enabled)
        if not enabled:
            self.setCursor(Qt.CursorShape.ArrowCursor)


class ResultsDialog(QDialog):
    def __init__(self, score, max_score, game_points, avg_time, focus_lost_count, leaders, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Результати тестування — QuizArena")
        self.setFixedSize(450, 560)
        self.setStyleSheet("""
            QDialog {
                background-color: #f4f6f9;
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #2d3436;
            }
            QLabel {
                color: #2d3436;
            }
            QPushButton {
                background-color: #0984e3;
                color: white;
                font-size: 11pt;
                font-weight: bold;
                border-radius: 8px;
                padding: 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0773c5;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(12)

        title_lbl = QLabel("🎉 Тест успішно завершено!")
        title_lbl.setStyleSheet("font-size: 15pt; font-weight: bold; color: #2d3436;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)

        grade_12 = round((score / max_score) * 12) if max_score > 0 else 0

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dfe6e9;
                border-radius: 12px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 15, 20, 15)
        card_layout.setSpacing(8)

        def create_stat_row(title, value, val_color="#2d3436"):
            w = QWidget()
            h = QHBoxLayout(w)
            h.setContentsMargins(0, 0, 0, 0)
            
            lbl_t = QLabel(title)
            lbl_t.setStyleSheet("font-size: 10pt; color: #636e72; font-weight: 600; background: transparent;")
            
            lbl_v = QLabel(value)
            lbl_v.setStyleSheet(f"font-size: 11pt; color: {val_color}; font-weight: bold; background: transparent;")
            lbl_v.setAlignment(Qt.AlignmentFlag.AlignRight)
            
            h.addWidget(lbl_t)
            h.addStretch()
            h.addWidget(lbl_v)
            return w

        card_layout.addWidget(create_stat_row("Правильні відповіді:", f"{score} з {max_score}"))
        card_layout.addWidget(create_stat_row("Оцінка (12-бальна):", f"{grade_12} / 12", "#00b894"))
        card_layout.addWidget(create_stat_row("Ігрові очки:", f"{game_points} 🏆", "#e17055"))
        card_layout.addWidget(create_stat_row("Середній час на питання:", f"{avg_time} сек."))
        card_layout.addWidget(create_stat_row("Фіксацій втрати фокусу:", f"{focus_lost_count} раз.", "#d63031" if focus_lost_count > 0 else "#2d3436"))

        layout.addWidget(card)

        leader_label = QLabel("<b>🥇 Таблиця лідерів (Top):</b>")
        leader_label.setStyleSheet("font-size: 11pt; color: #2d3436; margin-top: 5px;")
        layout.addWidget(leader_label)

        leaders_card = QFrame()
        leaders_card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dfe6e9;
                border-radius: 10px;
            }
        """)
        leaders_layout = QVBoxLayout(leaders_card)
        leaders_layout.setContentsMargins(15, 12, 15, 12)
        leaders_layout.setSpacing(6)
        
        if leaders:
            for idx, (name, pts) in enumerate(leaders, 1):
                medal = "🥇" if idx == 1 else ("🥈" if idx == 2 else "🥉")
                l_row = QLabel(f"{medal} <b>{idx}. {name}</b> — {pts} очок")
                l_row.setStyleSheet("font-size: 10pt; color: #2d3436; background: transparent;")
                leaders_layout.addWidget(l_row)
        else:
            no_l = QLabel("Ще немає результатів")
            no_l.setStyleSheet("color: #b2bec3; font-style: italic; background: transparent;")
            leaders_layout.addWidget(no_l)

        layout.addWidget(leaders_card)

        btn_close = QPushButton("Закрити")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)


class TestRunWindow(QWidget):
    def __init__(self, student_id, test_id, is_preview=False):
        super().__init__()
        self.student_id = student_id
        self.test_id = test_id
        self.is_preview = is_preview
        self.questions = []
        self.current_q_index = 0
        self.score = 0
        self.game_points = 0
        self.correct_streak = 0
        
        self.question_start_time = 0
        self.total_answer_time = 0.0
        self.focus_lost_count = 0
        self.is_answered = False
        
        self.load_test_data()
        self.initUI()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.time_left = self.time_limit
        self.timer.start(1000)
        self.question_start_time = time.time()

    def load_test_data(self):
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT title, time_limit FROM tests WHERE id = ?", (self.test_id,))
        test_info = cursor.fetchone()
        self.test_title = test_info[0] if test_info else "Тест"
        self.time_limit = test_info[1] if test_info and test_info[1] else 30
        
        cursor.execute("SELECT id, content, question_type FROM questions WHERE test_id = ?", (self.test_id,))
        raw_questions = cursor.fetchall()
        
        for q in raw_questions:
            q_id, content, q_type = q
            cursor.execute("SELECT id, content, is_correct FROM answers WHERE question_id = ?", (q_id,))
            answers = cursor.fetchall()
            self.questions.append({
                'id': q_id,
                'content': content,
                'type': q_type,
                'answers': answers
            })
        conn.close()

    def initUI(self):
        mode_title = " [ПЕРЕГЛЯД ВИКЛАДАЧА]" if self.is_preview else ""
        self.setWindowTitle(f"QuizArena — {self.test_title}{mode_title}")
        self.setStyleSheet("""
            QWidget {
                background-color: #f4f6f9;
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #2d3436;
            }
            QLabel#questionLabel {
                font-size: 14pt;
                font-weight: bold;
                color: #2d3436;
                padding: 20px;
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #dfe6e9;
            }
            QLabel#timerLabel {
                font-size: 12pt;
                font-weight: bold;
                color: #2d3436;
                background-color: #ffffff;
                border: 1px solid #dfe6e9;
                border-radius: 8px;
                padding: 6px 14px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(15)

        top_panel = QHBoxLayout()
        self.lbl_progress = QLabel("Питання 1 / 1")
        self.lbl_progress.setStyleSheet("font-size: 12pt; font-weight: bold; color: #636e72;")
        
        self.lbl_timer = QLabel(f"⏳ Час: {self.time_limit} сек")
        self.lbl_timer.setObjectName("timerLabel")
        self.lbl_timer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        top_panel.addWidget(self.lbl_progress)
        top_panel.addStretch()
        top_panel.addWidget(self.lbl_timer)
        layout.addLayout(top_panel)

        self.lbl_question = QLabel("Текст запитання...")
        self.lbl_question.setObjectName("questionLabel")
        self.lbl_question.setWordWrap(True)
        self.lbl_question.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_question)

        # Контейнер для плиток відповідей
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(15)
        layout.addLayout(self.grid_layout)
        
        self.load_question()

    def load_question(self):
        if self.current_q_index >= len(self.questions):
            self.finish_test()
            return
            
        self.is_answered = False
        q = self.questions[self.current_q_index]
        self.lbl_progress.setText(f"Питання {self.current_q_index + 1} / {len(self.questions)}")
        
        # Форматуємо текст питання
        formatted_question = format_long_text(q['content'], max_len=25)
        self.lbl_question.setText(formatted_question)
        self.lbl_question.setWordWrap(True)
        
        # Очищаємо попередні плитки відповідей з сітки
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        self.tile_widgets = []
        answers = q['answers']
        colors = ["#eb4d4b", "#3b82f6", "#f1c40f", "#2ecc71"]
        symbols = ["▲", "◆", "●", "■"]
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        
        for i, ans in enumerate(answers):
            if i < 4:
                tile = ClickableTile(colors[i], symbols[i], ans[1])
                tile.clicked.connect(lambda idx=i: self.handle_answer_click(idx))
                self.grid_layout.addWidget(tile, positions[i][0], positions[i][1])
                self.tile_widgets.append(tile)
                
        self.time_left = self.time_limit
        self.lbl_timer.setText(f"⏳ Час: {self.time_left} сек")
        self.question_start_time = time.time()

    def update_timer(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.lbl_timer.setText(f"⏳ Час: {self.time_left} сек")
        else:
            self.timer.stop()
            self.handle_answer_click(-1)

    def handle_answer_click(self, btn_index):
        if self.is_answered:
            return
        self.is_answered = True
        self.timer.stop()
        
        elapsed = time.time() - self.question_start_time
        self.total_answer_time += elapsed
        
        q = self.questions[self.current_q_index]
        answers = q['answers']
        correct_index = -1
        for idx, ans in enumerate(answers):
            if ans[2] == 1:
                correct_index = idx
                break
                
        is_correct = (btn_index == correct_index)
        
        for i, tile in enumerate(self.tile_widgets):
            tile.set_active(False)
            if i == correct_index:
                tile.setStyleSheet("background-color: #00b894; border-radius: 12px;")
            elif i == btn_index and not is_correct:
                tile.setStyleSheet("background-color: #d63031; border-radius: 12px;")
                
        if is_correct:
            self.score += 1
            self.correct_streak += 1
            streak_bonus = min(self.correct_streak * 50, 200)
            self.game_points += (500 + streak_bonus)
        else:
            self.correct_streak = 0
            
        QTimer.singleShot(1100, self.next_question)

    def next_question(self):
        self.current_q_index += 1
        self.timer.start(1000)
        self.load_question()

    def changeEvent(self, event):
        if event.type() == event.Type.ActivationChange and not self.isActiveWindow():
            if not self.is_preview and not self.is_answered:
                self.focus_lost_count += 1
        super().changeEvent(event)

    def finish_test(self):
        self.timer.stop()
        max_score = len(self.questions)
        avg_time = round(self.total_answer_time / max_score, 2) if max_score > 0 else 0.0
        
        leaders = []
        if not self.is_preview:
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO attempts (student_id, test_id, score, max_score, game_points, avg_time, focus_lost_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (self.student_id, self.test_id, self.score, max_score, self.game_points, avg_time, self.focus_lost_count))
            conn.commit()
            
            cursor.execute("""
                SELECT u.full_name, a.game_points 
                FROM attempts a 
                JOIN users u ON a.student_id = u.id 
                WHERE a.test_id = ? AND u.role != 'teacher'
                ORDER BY a.game_points DESC LIMIT 3
            """, (self.test_id,))
            leaders = cursor.fetchall()
            conn.close()
        else:
            leaders = [("Режим перегляду (Викладач)", self.game_points)]

        res_dialog = ResultsDialog(
            score=self.score,
            max_score=max_score,
            game_points=self.game_points,
            avg_time=avg_time,
            focus_lost_count=self.focus_lost_count,
            leaders=leaders,
            parent=self
        )
        res_dialog.exec()
        
        # Після закриття діалогу результатів повертаємо користувача до його кабінету замість закриття програми
        if self.is_preview:
            self.close()  # Викладач просто закриває тестовий перегляд
        else:
            from student_window import StudentWindow
            # Отримуємо ім'я студента з бази для коректного відкриття вікна
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            cursor.execute("SELECT full_name FROM users WHERE id = ?", (self.student_id,))
            st_data = cursor.fetchone()
            st_name = st_data[0] if st_data else "Студент"
            conn.close()
            
            self.student_win = StudentWindow(student_id=self.student_id, student_name=st_name)
            self.student_win.showMaximized()
            self.close()