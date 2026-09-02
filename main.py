import sys
import os
import json

# Set X11/XWayland platform environment variable before importing Qt
os.environ["QT_QPA_PLATFORM"] = "xcb"

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon, QPixmap

from asset_processor import process_reference_image
from sprite_manager import SpriteManager
from state_machine import PetBehaviorEngine
from pet_window import DesktopPet
from autostart_manager import is_autostart_enabled, set_autostart


class PetApp:
    def __init__(self, config_path: str = "config.json"):
        # Load configuration
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                self.config = json.load(f)
        else:
            self.config = {
                "pet_name": "UserPet",
                "reference_image_path": "assets/reference/user_pet_reference.png",
                "sprite_scale": 1.0,
                "walk_speed_px": 2,
                "frame_rate_ms": 100,
                "always_on_top": True,
                "sticky_all_workspaces": True,
                "behavior_interval": {"min_seconds": 3, "max_seconds": 8}
            }

        # Override env flag if defined in config
        if "environment_flags" in self.config:
            for k, v in self.config["environment_flags"].items():
                os.environ[k] = v

        # Process reference image if sprites do not exist
        if not os.path.exists("assets/sprites/idle"):
            process_reference_image(self.config.get("reference_image_path", "assets/reference/user_pet_reference.png"))

        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # Initialize sprite manager and behavior engine
        self.sprite_manager = SpriteManager(
            sprites_dir="assets/sprites",
            scale=self.config.get("sprite_scale", 1.0)
        )

        b_interval = self.config.get("behavior_interval", {"min_seconds": 3, "max_seconds": 8})
        self.engine = PetBehaviorEngine(
            min_seconds=b_interval.get("min_seconds", 3),
            max_seconds=b_interval.get("max_seconds", 8)
        )

        # Initialize pet window
        self.pet = DesktopPet(self.config, self.sprite_manager)

        # Connect signals
        self.engine.state_changed.connect(self.on_state_change)
        self.engine.vitals.vitals_updated.connect(self.pet.update_tooltip)

        self.pet.feed_requested.connect(self.on_feed_requested)
        self.pet.toggle_sleep_requested.connect(self.on_toggle_sleep_requested)
        self.pet.state_change_requested.connect(self.on_manual_state_change)

        # Setup Animation and Movement Loop
        self.walk_speed = self.config.get("walk_speed_px", 2)
        self.frame_rate_ms = self.config.get("frame_rate_ms", 100)

        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self.update_loop)
        self.anim_timer.start(self.frame_rate_ms)

        # Setup System Tray Icon
        self.setup_system_tray()

    def setup_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self.app)

        # Use first idle frame or fallback pixmap as tray icon
        tray_pixmap = self.sprite_manager.get_current_frame("idle")
        if not tray_pixmap.isNull():
            self.tray_icon.setIcon(QIcon(tray_pixmap))

        self.tray_icon.setToolTip(f"{self.config.get('pet_name', 'UserPet')} Mascot")

        tray_menu = QMenu()
        toggle_vis_act = tray_menu.addAction("Toggle Mascot Visibility")
        toggle_vis_act.triggered.connect(self.toggle_visibility)

        feed_act = tray_menu.addAction("Feed Mascot")
        feed_act.triggered.connect(self.on_feed_requested)

        tray_menu.addSeparator()

        quit_act = tray_menu.addAction("Exit App")
        quit_act.triggered.connect(self.app.quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def toggle_visibility(self):
        if self.pet.isVisible():
            self.pet.hide()
        else:
            self.pet.show()

    def on_state_change(self, new_state: str):
        self.pet.set_state(new_state)

    def on_manual_state_change(self, new_state: str):
        self.engine.set_state(new_state)

    def on_feed_requested(self):
        self.engine.vitals.feed()

    def on_toggle_sleep_requested(self):
        if self.engine.current_state == "sleep":
            self.engine.set_state("idle")
        else:
            self.engine.set_state("sleep")

    def update_loop(self):
        # Update frame animation
        self.pet.update_frame()

        # Handle horizontal roaming movement
        current_state = self.engine.current_state
        if current_state in ["walk_left", "walk_right"]:
            # Check edge bounce
            bounced_state = self.pet.check_boundary_bounce(self.walk_speed)
            if bounced_state:
                self.engine.set_state(bounced_state)
            else:
                pos = self.pet.pos()
                dx = -self.walk_speed if current_state == "walk_left" else self.walk_speed
                self.pet.move(pos.x() + dx, pos.y())

    def run(self):
        return self.app.exec()


if __name__ == "__main__":
    app = PetApp()
    sys.exit(app.run())
