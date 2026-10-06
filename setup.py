#!/usr/bin/env python3
"""
setup.py — One-time setup script.
Installs fonts into the fonts/ folder (uses system fonts as a reliable source).
Run once before starting the automation.
"""
import shutil
from pathlib import Path

FONTS_DIR = Path(__file__).parent / "fonts"
FONTS_DIR.mkdir(exist_ok=True)

# Map our font names → system font paths (DejaVu Sans is installed on all Ubuntu/Debian)
SYSTEM_FONTS = {
    "Roboto-Black.ttf":   [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ],
    "Roboto-Bold.ttf":    [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ],
    "Roboto-Regular.ttf": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ],
}

print("Setting up fonts…")
for filename, candidates in SYSTEM_FONTS.items():
    dest = FONTS_DIR / filename
    if dest.exists() and dest.stat().st_size > 1000:
        print(f"  ✓ {filename} already set up")
        continue
    copied = False
    for src in candidates:
        if Path(src).exists():
            shutil.copy(src, dest)
            print(f"  ✓ {filename} (from {Path(src).name})")
            copied = True
            break
    if not copied:
        print(f"  ⚠ {filename} — not found, will fall back to default font")

print("\nChecking .env file…")
env_file = Path(__file__).parent / ".env"
env_example = Path(__file__).parent / ".env.example"
if not env_file.exists():
    import shutil
    shutil.copy(env_example, env_file)
    print("  ✓ Created .env from .env.example — please fill in your API keys!")
else:
    print("  ✓ .env already exists")

Path("logs").mkdir(exist_ok=True)
Path("output").mkdir(exist_ok=True)

print("\n✅ Setup complete!")
print("Next steps:")
print("  1. Edit .env with your API keys")
print("  2. Run: python3 test_pipeline.py   ← test with a sample image")
print("  3. Run: python3 main.py             ← run the full automation")
