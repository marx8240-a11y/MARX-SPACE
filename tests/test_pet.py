import os
import json
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from asset_processor import process_reference_image, remove_background_and_crop
from sprite_manager import SpriteManager
from state_machine import PetBehaviorEngine, VitalsSystem
from pet_window import DesktopPet
from autostart_manager import set_autostart, is_autostart_enabled, DESKTOP_FILE_PATH


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_asset_processor_and_sprites(qapp):
    ref_path = "assets/reference/user_pet_reference.png"
    assert os.path.exists(ref_path)

    mascot = remove_background_and_crop(ref_path)
    assert mascot is not None
    assert mascot.mode == "RGBA"

    process_reference_image(ref_path)

    for state in ["idle", "walk_left", "walk_right", "sleep"]:
        dir_path = os.path.join("assets/sprites", state)
        assert os.path.exists(dir_path)
        files = os.listdir(dir_path)
        assert len(files) > 0


def test_sprite_manager(qapp):
    sm = SpriteManager(scale=1.0)
    assert len(sm.frames["idle"]) > 0
    frame0 = sm.get_current_frame("idle")
    assert not frame0.isNull()

    frame1 = sm.advance_frame("idle")
    assert not frame1.isNull()


def test_vitals_and_behavior_engine(qapp):
    vitals = VitalsSystem()
    initial_status = vitals.get_status()
    assert initial_status["hunger"] == 100.0
    assert initial_status["energy"] == 100.0

    vitals.tick()
    status_after_tick = vitals.get_status()
    assert status_after_tick["hunger"] < 100.0

    vitals.feed()
    assert vitals.hunger == 100.0

    engine = PetBehaviorEngine(min_seconds=1, max_seconds=2)
    assert engine.current_state in ["idle", "walk_left", "walk_right", "sleep"]

    engine.set_state("sleep")
    assert engine.current_state == "sleep"


def test_desktop_pet_window(qapp):
    config = {
        "pet_name": "TestMascot",
        "always_on_top": True,
        "sticky_all_workspaces": True,
        "sprite_scale": 1.0
    }
    sm = SpriteManager()
    pet = DesktopPet(config, sm)

    assert pet.windowTitle() == "TestMascot"
    assert pet.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    assert bool(pet.windowFlags() & Qt.WindowType.X11BypassWindowManagerHint)

    pet.set_state("walk_right")
    assert pet.current_state == "walk_right"

    pet.clamp_to_screen()


def test_autostart_manager(tmp_path):
    # Enable autostart
    enabled = set_autostart(True)
    assert enabled
    assert is_autostart_enabled()

    # Disable autostart
    disabled = set_autostart(False)
    assert not disabled
    assert not is_autostart_enabled()
