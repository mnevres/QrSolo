from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer

class ToastNotification(QWidget):
    def __init__(self, parent, message, duration=3000, color="#32d74b"):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.layout = QHBoxLayout(self)
        self.label = QLabel(message)
        self.label.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(20, 20, 23, 230);
                color: white;
                border: 1px solid {color};
                border-radius: 15px;
                padding: 12px 25px;
                font-size: 14px;
                font-weight: 600;
            }}
        """)
        self.layout.addWidget(self.label)
        
        # Opacity effect for animation
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        
        # Animation
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(400)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.hide_toast)
        
        self.duration = duration

    def show_toast(self):
        # Position at the center of parent
        if self.parent():
            self.adjustSize()
            parent_rect = self.parent().frameGeometry()
            center_point = parent_rect.center()
            
            # Calculate top-left based on center
            x = center_point.x() - self.width() // 2
            y = center_point.y() - self.height() // 2
            self.move(x, y)
            
        self.show()
        self.anim.start()
        self.timer.start(self.duration)

    def hide_toast(self):
        self.anim.setDirection(QPropertyAnimation.Backward)
        self.anim.finished.connect(self.deleteLater)
        self.anim.start()
