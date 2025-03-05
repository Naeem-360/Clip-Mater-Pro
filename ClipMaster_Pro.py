import sys
import pyperclip
import time
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QTextEdit)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QCursor

clipboard_history = []

class ClipboardThread(QThread):
    new_clipboard = pyqtSignal(str)
    
    def run(self):
        last_copied = ""
        while True:
            try:
                copied_text = pyperclip.paste().strip()
                if copied_text and copied_text != last_copied:
                    self.new_clipboard.emit(copied_text)
                    last_copied = copied_text
                    time.sleep(0.5)
                time.sleep(1)
            except Exception as e:
                print(f"Clipboard error: {e}")
                time.sleep(1)

class ClipboardGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.old_pos = None
        self.click_start_pos = None
        self.is_shrunk = False
        self.shrunk_size = (80, 80)
        self.resizing = False
        self.resize_start_pos = None
        self.resize_edge = None
        self.initUI()
        pyperclip.copy("")
        self.clipboard_thread = ClipboardThread(self)
        self.clipboard_thread.new_clipboard.connect(self.add_to_history)
        self.clipboard_thread.start()

    def initUI(self):
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(200, 200, 600, 800)  
        self.setMinimumSize(300, 400)  

        self.main_widget = QWidget(self)
        self.main_widget.setStyleSheet("background-color: rgba(0, 0, 0, 100); border-radius: 10px;")
        self.main_layout = QVBoxLayout(self.main_widget)

        self.title = QLabel("Clipboard Manager", self.main_widget)
        self.title.setFont(QFont("Arial", 20, QFont.Bold))
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("""
            color: white;
            text-shadow: 0 0 5px blue;
            background-color: rgba(0, 0, 0, 150);
            padding: 5px;
            border-radius: 5px;
        """)
        self.main_layout.addWidget(self.title)
        self.history_text = QTextEdit(self.main_widget)
        self.history_text.setReadOnly(True)
        self.history_text.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0, 0, 0, 150);
                color: white;
                border: 2px solid blue;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        self.history_text.setFont(QFont("Arial", 12))
        self.update_text_cursor()
        self.history_text.textChanged.connect(self.update_text_cursor)
        self.main_layout.addWidget(self.history_text)

        self.btn_layout = QHBoxLayout()

        self.clear_btn = QPushButton("Clear History", self.main_widget)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 150);
                border: 2px solid blue;
                color: white;
                font-size: 14px;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgba(30, 144, 255, 200);
            }
        """)
        self.clear_btn.clicked.connect(self.clear_history)
        self.btn_layout.addWidget(self.clear_btn)

        self.stop_btn = QPushButton("Stop Manager", self.main_widget)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 150);
                border: 2px solid blue;
                color: white;
                font-size: 14px;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 69, 0, 200);
            }
        """)
        self.stop_btn.clicked.connect(self.stop_manager)
        self.btn_layout.addWidget(self.stop_btn)

        self.shrink_btn = QPushButton("Shrink", self.main_widget)
        self.shrink_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 150);
                border: 2px solid blue;
                color: white;
                font-size: 14px;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgba(128, 0, 128, 200);
            }
        """)
        self.shrink_btn.clicked.connect(self.toggle_shrink)
        self.btn_layout.addWidget(self.shrink_btn)

        self.main_layout.addLayout(self.btn_layout)
        self.main_widget.setLayout(self.main_layout)
        self.main_widget.resize(self.size()) 

        self.animation_radius = 30
        self.animation_step = 2
        QTimer(self, timeout=self.update_animation).start(50)

        self.original_geometry = self.geometry()

    def update_text_cursor(self):
        if self.history_text.toPlainText().strip():
            self.history_text.setCursor(QCursor(Qt.IBeamCursor))
        else:
            self.history_text.setCursor(QCursor(Qt.ArrowCursor))

    def enterEvent(self, event):
        self.update_cursor(event.pos())

    def leaveEvent(self, event):
        self.setCursor(Qt.ArrowCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            child = self.childAt(pos)
            is_over_button = child in (self.clear_btn, self.stop_btn, self.shrink_btn)
            
            if not is_over_button:
                self.old_pos = event.globalPos()
                self.click_start_pos = event.globalPos()

            if not self.is_shrunk:
                self.resize_edge = self.get_resize_edge(pos)
                if self.resize_edge:
                    self.resizing = True
                    self.resize_start_pos = event.globalPos()
                    self.original_geometry = self.geometry()
                else:
                    self.resizing = False

    def mouseMoveEvent(self, event):
        pos = event.pos()
        self.update_cursor(pos)  

        if self.old_pos is not None:
            child = self.childAt(pos)
            is_over_button = child in (self.clear_btn, self.stop_btn, self.shrink_btn)
            
            if not is_over_button:
                delta = event.globalPos() - self.old_pos
                if self.is_shrunk:
                    self.move(self.x() + delta.x(), self.y() + delta.y())
                    self.old_pos = event.globalPos()
                elif self.resizing and self.resize_edge and self.resize_start_pos:
                    delta_resize = event.globalPos() - self.resize_start_pos
                    rect = QRect(self.original_geometry)

                    if self.resize_edge & Qt.LeftEdge:
                        rect.setLeft(rect.left() + delta_resize.x())
                    if self.resize_edge & Qt.RightEdge:
                        rect.setRight(rect.right() + delta_resize.x())
                    if self.resize_edge & Qt.TopEdge:
                        rect.setTop(rect.top() + delta_resize.y())
                    if self.resize_edge & Qt.BottomEdge:
                        rect.setBottom(rect.bottom() + delta_resize.y())

                    if rect.width() >= self.minimumWidth() and rect.height() >= self.minimumHeight():
                        self.setGeometry(rect)
                        self.main_widget.resize(self.size())
                else:
                    self.move(self.x() + delta.x(), self.y() + delta.y())
                    self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_shrunk:
            if self.click_start_pos is not None:
                delta = event.globalPos() - self.click_start_pos
                if abs(delta.x()) < 5 and abs(delta.y()) < 5:
                    self.toggle_shrink()
            self.old_pos = None
            self.click_start_pos = None
        self.resize_start_pos = None
        self.resize_edge = None
        self.resizing = False
        self.update_cursor(event.pos())
        QApplication.processEvents()  

    def update_cursor(self, pos):
        if self.is_shrunk:
            self.setCursor(Qt.OpenHandCursor)
        
        else:
            child = self.childAt(pos)
            is_over_button = child in (self.clear_btn, self.stop_btn, self.shrink_btn)
            if is_over_button:
                self.setCursor(Qt.ArrowCursor)
               
            else:
                edge = self.get_resize_edge(pos)
                if edge == (Qt.LeftEdge | Qt.TopEdge) or edge == (Qt.RightEdge | Qt.BottomEdge):
                    self.setCursor(Qt.SizeFDiagCursor)
                    
                elif edge == (Qt.RightEdge | Qt.TopEdge) or edge == (Qt.LeftEdge | Qt.BottomEdge):
                    self.setCursor(Qt.SizeBDiagCursor)
                  
                elif edge == Qt.LeftEdge or edge == Qt.RightEdge:
                    self.setCursor(Qt.SizeHorCursor)
                   
                elif edge == Qt.TopEdge or edge == Qt.BottomEdge:
                    self.setCursor(Qt.SizeVerCursor)
                   
                else:
                    self.setCursor(Qt.ArrowCursor)
                

    def get_resize_edge(self, pos):
        edge = 0
        margin = 10  
        if pos.x() < margin:
            edge |= Qt.LeftEdge
        elif pos.x() > self.width() - margin:
            edge |= Qt.RightEdge
        if pos.y() < margin:
            edge |= Qt.TopEdge
        elif pos.y() > self.height() - margin:
            edge |= Qt.BottomEdge
        return edge

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(30, 144, 255, 200), 2))
        if self.is_shrunk:
            painter.setBrush(QColor(0, 0, 0, 150))
            painter.drawEllipse(0, 0, self.shrunk_size[0], self.shrunk_size[1])
        else:
            center_x, center_y = self.width() // 2, self.height() // 2
            painter.drawEllipse(center_x - self.animation_radius, center_y - self.animation_radius, 
                              self.animation_radius * 2, self.animation_radius * 2)

    def update_animation(self):
        if not self.is_shrunk:
            self.animation_radius += self.animation_step
            if self.animation_radius >= 40 or self.animation_radius <= 20:
                self.animation_step = -self.animation_step
        self.update()

    def toggle_shrink(self):
        if self.is_shrunk:
            self.setGeometry(self.original_geometry)
            self.main_widget.show()
            self.shrink_btn.setText("Shrink")
            self.is_shrunk = False
            self.main_widget.resize(self.size())
        else:
            self.original_geometry = self.geometry()
            self.resize(*self.shrunk_size)
            self.main_widget.hide()
            self.shrink_btn.setText("Expand")
            self.is_shrunk = True
        self.update()

    def add_to_history(self, text):
        if text not in clipboard_history and text.strip():
            clipboard_history.insert(0, text)
            current_text = self.history_text.toPlainText()
            if current_text:
                new_text = f"{text}\n{' ' * 20}\n{current_text}"
            else:
                new_text = text
            self.history_text.setPlainText(new_text)
            print(f"New Copy: {text}")

    def clear_history(self):
        clipboard_history.clear()
        self.history_text.clear()
        print("Clipboard history cleared.")

    def stop_manager(self):
        if hasattr(self, 'clipboard_thread'):
            self.clipboard_thread.terminate()
            self.clipboard_thread.wait()
            print("\nClipboard Manager Stopped.")
            print("Clipboard History:")
            for i, text in enumerate(clipboard_history, 1):
                print(f"{i}. {text}")
        QApplication.quit()

def main():
    app = QApplication(sys.argv)
    window = ClipboardGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
