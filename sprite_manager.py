import os
from PyQt6.QtGui import QPixmap, QTransform
from PyQt6.QtCore import QSize

class SpriteManager:
    def __init__(self, sprites_dir: str = "assets/sprites", scale: float = 1.0):
        self.sprites_dir = sprites_dir
        self.scale = scale
        self.frames = {
            "idle": [],
            "walk_left": [],
            "walk_right": [],
            "sleep": []
        }
        self.frame_indices = {
            "idle": 0,
            "walk_left": 0,
            "walk_right": 0,
            "sleep": 0
        }
        self.load_sprites()

    def load_sprites(self):
        for state in self.frames.keys():
            dir_path = os.path.join(self.sprites_dir, state)
            if not os.path.exists(dir_path):
                continue

            # Find and sort frame files e.g. 0.png, 1.png...
            file_names = sorted(
                [f for f in os.listdir(dir_path) if f.endswith(".png")],
                key=lambda x: int(os.path.splitext(x)[0]) if os.path.splitext(x)[0].isdigit() else x
            )

            for file_name in file_names:
                file_path = os.path.join(dir_path, file_name)
                pixmap = QPixmap(file_path)
                if not pixmap.isNull() and self.scale != 1.0:
                    new_width = int(pixmap.width() * self.scale)
                    new_height = int(pixmap.height() * self.scale)
                    pixmap = pixmap.scaled(
                        new_width, new_height,
                        transformMode=True # FastTransformation / SmoothTransformation
                    )
                self.frames[state].append(pixmap)

    def get_current_frame(self, state: str) -> QPixmap:
        if state not in self.frames or not self.frames[state]:
            return QPixmap()
        idx = self.frame_indices.get(state, 0) % len(self.frames[state])
        return self.frames[state][idx]

    def advance_frame(self, state: str) -> QPixmap:
        if state not in self.frames or not self.frames[state]:
            return QPixmap()
        self.frame_indices[state] = (self.frame_indices.get(state, 0) + 1) % len(self.frames[state])
        return self.get_current_frame(state)
