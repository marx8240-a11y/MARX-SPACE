# Interactive Desktop Pet for Fedora Linux

An interactive, transparent, floating desktop mascot for Fedora Linux Workstation (GNOME / Wayland & X11). The pet roams your workspace, responds to mouse inputs, tracks vitals (Hunger, Energy, Happiness), and executes autonomous behavior loops.

---

## Features

- **Transparent & Frameless Window:** Renders directly on top of active desktop windows without borders or black backgrounds (`QT_QPA_PLATFORM=xcb`).
- **Asset Processing Engine:** Automatically processes user reference images (`assets/reference/user_pet_reference.png`), removes background pixels for alpha transparency, crops tightly, and generates frame sequences (`idle`, `walk_left`, `walk_right`, `sleep`).
- **Autonomous Behavior Engine:** Finite state machine with randomized timers (3–8s) to switch between idle, walking, and sleeping states.
- **Vitals System:** Tracks Hunger, Energy, and Happiness. The pet will automatically sleep when exhausted, and vitals degrade gracefully over time.
- **Interactive Mechanics:**
  - **Left-Click & Drag:** Relocate the pet anywhere across single or multi-monitor setups.
  - **Right-Click Context Menu:** Access options to Feed Pet, Put to Sleep / Wake Up, Change State manually, toggle Autostart on login, and Exit.
  - **Hover Tooltips:** Hover over the mascot to inspect real-time vitals and state status.
- **Fedora Integration:**
  - System tray icon for background control and visibility toggling.
  - Automatic `.desktop` launcher creation in `~/.config/autostart/` for login autostart.

---

## Prerequisites

- **Operating System:** Fedora Linux Workstation (or any Linux distro running GNOME / Wayland / X11)
- **Python:** Python 3.10 or higher
- **System Dependencies:** `xcb` libraries (pre-installed on standard Fedora Workstation)

---

## Installation & Setup Guide

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/desktop-pet.git
cd desktop-pet
```

### 2. Create and Activate a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Required Dependencies
```bash
pip install PyQt6 Pillow numpy opencv-python pytest pytest-qt
```

---

## Adding Your Custom Mascot Image

1. Place your mascot source image in `assets/reference/user_pet_reference.png`.
2. (Optional) Run the asset processor manually to inspect generated sprites:
   ```bash
   python3 asset_processor.py
   ```
   *Note: If `assets/sprites/` does not exist when launching `main.py`, the asset processor will automatically run.*

---

## How to Run the Desktop Pet

Run the application entry point:
```bash
python3 main.py
```

### Controls & Actions
- **Move Mascot:** Click and hold the **Left Mouse Button** on the pet to drag it around your screen.
- **Context Menu:** **Right-Click** on the mascot to open options:
  - 🍖 **Feed Pet:** Increases hunger and happiness.
  - 💤 **Put to Sleep / ⏰ Wake Up:** Toggle sleep state manually.
  - 🔄 **Change State:** Force state to `Idle`, `Walk Left`, `Walk Right`, or `Sleep`.
  - 🚀 **Autostart on Login:** Toggle automatic launch upon Fedora login.
  - ❌ **Exit:** Terminate the pet application.
- **System Tray:** Click the tray icon to toggle pet visibility or exit.

---

## Configuration (`config.json`)

Customize runtime parameters in `config.json`:

```json
{
  "pet_name": "UserPet",
  "reference_image_path": "assets/reference/user_pet_reference.png",
  "sprite_scale": 1.0,
  "walk_speed_px": 2,
  "frame_rate_ms": 100,
  "always_on_top": true,
  "behavior_interval": {
    "min_seconds": 3,
    "max_seconds": 8
  },
  "environment_flags": {
    "QT_QPA_PLATFORM": "xcb"
  }
}
```

---

## Running Tests

Run the PyTest suite in offscreen mode:
```bash
PYTHONPATH=. QT_QPA_PLATFORM=offscreen pytest tests/test_pet.py
```

---

## Project Structure

```
desktop-pet/
├── assets/
│   ├── reference/
│   │   └── user_pet_reference.png   # Mascot source image
│   └── sprites/                     # Generated frame sequences
│       ├── idle/
│       ├── walk_left/
│       ├── walk_right/
│       └── sleep/
├── asset_processor.py               # Background transparency & sprite cutter
├── autostart_manager.py             # ~/.config/autostart/.desktop manager
├── config.json                      # Configuration & mascot metadata
├── main.py                          # Main entry point & app lifecycle
├── pet_window.py                    # Translucent GUI window & mouse event handlers
├── sprite_manager.py                # Frame loader & frame cycler
├── state_machine.py                 # Autonomous AI engine & vitals system
├── tests/
│   └── test_pet.py                  # PyTest verification test suite
└── README.md                        # Documentation & setup guide
```
