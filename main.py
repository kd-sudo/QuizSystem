import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from auth import AuthWindow

def handle_exception(exc_type, exc_value, exc_tb):
    tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(tb_str)
    QMessageBox.critical(None, "Критична помилка", f"Сталася непередбачувана помилка:\n{exc_value}")

if __name__ == "__main__":
    sys.excepthook = handle_exception
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    auth_window = AuthWindow()
    auth_window.resize(1050, 700)
    
    # Центруємо вікно на екрані
    screen = app.primaryScreen().geometry()
    auth_window.move(
        (screen.width() - auth_window.width()) // 2,
        (screen.height() - auth_window.height()) // 2
    )
    
    auth_window.show()
    
    sys.exit(app.exec())