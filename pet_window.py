import sys
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtWidgets import QWidget, QLabel, QMenu, QGraphicsDropShadowEffect
from PyQt6.QtGui import QMouseEvent, QAction, QColor, QScreen, QGuiApplication
from autostart_manager import is_autostart_enabled, set_autostart

class DesktopPet(QWidget):
    feed_requested = pyqtSignal()
    toggle_sleep_requested = pyqtSignal()
    state_change_requested = pyqtSignal(str)

    def __init__(self, config: dict, sprite_manager):
        super().__init__()
        self.config = config
        self.sprite_manager = sprite_manager
        self.pet_name = config.get("pet_name", "UserPet")
        self.drag_position = QPoint()
        self.current_state = "idle"

        self.init_ui()

    def init_ui(self):
        # Frameless, Always on Top, Translucent background
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.SubWindow
        if self.config.get("always_on_top", True):
            flags |= Qt.WindowType.WindowStaysOnTopHint

        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Initial frame display
        first_frame = self.sprite_manager.get_current_frame(self.current_state)
        if not first_frame.isNull():
            self.label.setPixmap(first_frame)
            self.resize(first_frame.size())

        self.setWindowTitle(self.pet_name)
        self.update_tooltip({"hunger": 100, "energy": 100, "happiness": 100})
        self.show()

    def set_state(self, state: str):
        self.current_state = state
        self.update_frame()

    def update_frame(self):
        pixmap = self.sprite_manager.advance_frame(self.current_state)
        if not pixmap.isNull():
            self.label.setPixmap(pixmap)
            self.resize(pixmap.size())

    def update_tooltip(self, vitals: dict):
        tooltip = (
            f"<b>{self.pet_name}</b><br/>"
            f"State: {self.current_state}<br/>"
            f"Hunger: {vitals.get('hunger', 100)}%<br/>"
            f"Energy: {vitals.get('energy', 100)}%<br/>"
            f"Happiness: {vitals.get('happiness', 100)}%"
        )
        self.setToolTip(tooltip)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self.drag_position
            self.move(new_pos)
            event.accept()

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        name_action = QAction(f"🐾 {self.pet_name}", self)
        name_action.setEnabled(False)
        menu.addAction(name_action)
        menu.addSeparator()

        feed_action = menu.addAction("🍖 Feed Pet")

        if self.current_state == "sleep":
            sleep_action = menu.addAction("⏰ Wake Up")
        else:
            sleep_action = menu.addAction("💤 Put to Sleep")

        # Change state sub-menu
        state_menu = menu.addMenu("🔄 Change State")
        idle_act = state_menu.addAction("Idle")
        walk_l_act = state_menu.addAction("Walk Left")
        walk_r_act = state_menu.addAction("Walk Right")
        sleep_act = state_menu.addAction("Sleep")

        menu.addSeparator()

        # Autostart toggle
        autostart_act = QAction("🚀 Autostart on Login", self)
        autostart_act.setCheckable(True)
        autostart_act.setChecked(is_autostart_enabled())
        menu.addAction(autostart_act)

        menu.addSeparator()
        quit_action = menu.addAction("❌ Exit")

        action = menu.exec(self.mapToGlobal(event.pos()))

        if action == feed_action:
            self.feed_requested.emit()
        elif action == sleep_action:
            self.toggle_sleep_requested.emit()
        elif action == idle_act:
            self.state_change_requested.emit("idle")
        elif action == walk_l_act:
            self.state_change_requested.emit("walk_left")
        elif action == walk_r_act:
            self.state_change_requested.emit("walk_right")
        elif action == sleep_act:
            self.state_change_requested.emit("sleep")
        elif action == autostart_act:
            set_autostart(autostart_act.isChecked())
        elif action == quit_action:
            sys.exit()

    def clamp_to_screen(self):
        """
        Keeps pet within monitor/screen bounds across multi-monitor setups.
        """
        screen = QGuiApplication.screenAt(self.geometry().center())
        if not screen:
            screen = QGuiApplication.primaryScreen()
        if not screen:
            return

        geo = screen.availableGeometry()
        x = max(geo.left(), min(self.x(), geo.right() - self.width()))
        y = max(geo.top(), min(self.y(), geo.bottom() - self.height()))
        if x != self.x() or y != self.y():
            self.move(x, y)

    def check_boundary_bounce(self, walk_speed: int) -> str | None:
        """
        Checks if pet collides with screen bounds while walking and returns new reversed direction if bounced.
        """
        screen = QGuiApplication.screenAt(self.geometry().center())
        if not screen:
            screen = QGuiApplication.primaryScreen()
        if not screen:
            return None

        geo = screen.availableGeometry()
        current_x = self.x()

        if self.current_state == "walk_left" and current_x - walk_speed <= geo.left():
            return "walk_right"
        elif self.current_state == "walk_right" and current_x + self.width() + walk_speed >= geo.right():
            return "walk_left"

        return None
