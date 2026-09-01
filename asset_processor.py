import os
import math
import numpy as np
from PIL import Image, ImageOps

def remove_background_and_crop(image_path: str, tolerance: float = 40.0) -> Image.Image:
    """
    Loads image, detects background color from corners, makes background transparent,
    and crops tightly around the non-transparent mascot subject.
    """
    img = Image.open(image_path).convert("RGBA")
    arr = np.array(img, dtype=np.float32) # (H, W, 4)
    h, w, _ = arr.shape

    # Sample corner pixels to determine background color (RGB)
    corners = np.array([
        arr[0, 0, :3],
        arr[0, w - 1, :3],
        arr[h - 1, 0, :3],
        arr[h - 1, w - 1, :3]
    ])
    avg_bg = np.mean(corners, axis=0) # [r, g, b]

    # Calculate Euclidean distance from avg_bg for every pixel
    diff = arr[:, :, :3] - avg_bg
    dist = np.sqrt(np.sum(diff ** 2, axis=2))

    # Mask alpha channel
    alpha = arr[:, :, 3]
    # Fully transparent where distance < tolerance
    alpha[dist < tolerance] = 0
    # Soft edges where tolerance <= distance < tolerance + 30
    feather_mask = (dist >= tolerance) & (dist < tolerance + 30)
    alpha[feather_mask] = 255.0 * ((dist[feather_mask] - tolerance) / 30.0)

    arr[:, :, 3] = np.clip(alpha, 0, 255)

    out_img = Image.fromarray(arr.astype(np.uint8), mode="RGBA")

    # Crop bounding box of non-transparent region
    bbox = out_img.getbbox()
    if bbox:
        out_img = out_img.crop(bbox)

    return out_img

def generate_sprite_sheets(base_img: Image.Image, output_dir: str = "assets/sprites", target_size: tuple[int, int] = (128, 128)):
    """
    Generates frame sequences for idle, walk_left, walk_right, and sleep states.
    """
    base_scaled = base_img.copy()
    base_scaled.thumbnail((100, 100), Image.Resampling.LANCZOS)

    os.makedirs(os.path.join(output_dir, "idle"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "walk_left"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "walk_right"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "sleep"), exist_ok=True)

    def create_canvas(sprite: Image.Image, offset_x: int = 0, offset_y: int = 0, angle: float = 0.0) -> Image.Image:
        canvas = Image.new("RGBA", target_size, (0, 0, 0, 0))
        rotated = sprite.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False)
        w, h = rotated.size
        px = (target_size[0] - w) // 2 + offset_x
        py = (target_size[1] - h) // 2 + offset_y
        canvas.paste(rotated, (px, py), rotated)
        return canvas

    # 1. IDLE frames (gentle vertical bobbing)
    idle_offsets = [0, -2, -4, -2, 0, 2]
    for idx, offset in enumerate(idle_offsets):
        frame = create_canvas(base_scaled, offset_y=offset)
        frame.save(os.path.join(output_dir, "idle", f"{idx}.png"))

    # 2. WALK_RIGHT frames (side tilt + bounce)
    walk_angles = [0, 5, 0, -5]
    walk_y_offsets = [0, -3, 0, -3]
    for idx, (angle, y_off) in enumerate(zip(walk_angles, walk_y_offsets)):
        frame = create_canvas(base_scaled, offset_y=y_off, angle=angle)
        frame.save(os.path.join(output_dir, "walk_right", f"{idx}.png"))

    # 3. WALK_LEFT frames (horizontally flipped walk_right)
    base_flipped = ImageOps.mirror(base_scaled)
    for idx, (angle, y_off) in enumerate(zip(walk_angles, walk_y_offsets)):
        frame = create_canvas(base_flipped, offset_y=y_off, angle=-angle)
        frame.save(os.path.join(output_dir, "walk_left", f"{idx}.png"))

    # 4. SLEEP frames (slightly compressed/tilted pose)
    sleep_base = base_scaled.rotate(-15, resample=Image.Resampling.BICUBIC, expand=False)
    sleep_offsets = [4, 6, 8, 6]
    for idx, y_off in enumerate(sleep_offsets):
        frame = create_canvas(sleep_base, offset_y=y_off)
        frame.save(os.path.join(output_dir, "sleep", f"{idx}.png"))

def process_reference_image(reference_path: str = "assets/reference/user_pet_reference.png", sprites_dir: str = "assets/sprites"):
    if not os.path.exists(reference_path):
        raise FileNotFoundError(f"Reference image not found at {reference_path}")
    mascot = remove_background_and_crop(reference_path)
    generate_sprite_sheets(mascot, sprites_dir)

if __name__ == "__main__":
    process_reference_image()
