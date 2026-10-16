#!/usr/bin/env python3
"""Create a merged E1004 image and ESP Web Tools manifest from a firmware build."""

import argparse
import hashlib
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_OFFSET = 0x10000
APP_SLOT_SIZE = 0x3F0000
PARTS = (
    ("bootloader.bin", 0x0000, 0x8000),
    ("partitions.bin", 0x8000, 0x6000),
    ("boot_app0.bin", 0xE000, 0x2000),
    ("firmware.bin", APP_OFFSET, APP_SLOT_SIZE),
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", required=True, type=Path,
                        help="PlatformIO .pio/build/reterminal_e1004 directory")
    parser.add_argument("--version", required=True,
                        help="Public release version shown by the installer")
    parser.add_argument("--boot-app0", type=Path,
                        help="Override the boot_app0.bin path from PlatformIO")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "firmware")
    args = parser.parse_args()

    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,63}", args.version):
        parser.error("version must be 1–64 letters, numbers, dots, dashes, pluses or underscores")

    packages_dir = Path(os.environ.get("PLATFORMIO_PACKAGES_DIR", Path.home() / ".platformio/packages"))
    boot_app0 = args.boot_app0 or (packages_dir / "framework-arduinoespressif32" /
                                   "tools/partitions/boot_app0.bin")
    paths = {
        "bootloader.bin": args.build_dir / "bootloader.bin",
        "partitions.bin": args.build_dir / "partitions.bin",
        "boot_app0.bin": boot_app0,
        "firmware.bin": args.build_dir / "firmware.bin",
    }
    pieces = {}
    for name, _, limit in PARTS:
        try:
            piece = paths[name].read_bytes()
        except OSError as exc:
            parser.error(f"cannot read {name}: {exc}")
        if not piece or len(piece) > limit:
            parser.error(f"{name} must be between 1 and {limit} bytes")
        pieces[name] = piece

    if pieces["bootloader.bin"][0] != 0xE9 or pieces["firmware.bin"][0] != 0xE9:
        parser.error("bootloader.bin and firmware.bin must be ESP images")
    if not pieces["partitions.bin"].startswith(b"\xaa\x50"):
        parser.error("partitions.bin does not have an ESP partition-table marker")

    image = bytearray(b"\xff" * (APP_OFFSET + len(pieces["firmware.bin"])))
    for name, offset, _ in PARTS:
        piece = pieces[name]
        image[offset:offset + len(piece)] = piece

    printable_strings = re.findall(rb"[ -~]{8,}", image)
    absolute_build_path = re.compile(rb"(?<![A-Za-z0-9])/(?:Users|home|mnt|private|tmp)/[A-Za-z0-9._-]+")
    if any(absolute_build_path.search(item) for item in printable_strings):
        parser.error("image contains absolute build paths; rebuild with -ffile-prefix-map before publishing")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    factory_path = args.output_dir / "factory.bin"
    factory_path.write_bytes(image)
    manifest = {
        "name": "NYTDisplay",
        "version": args.version,
        "new_install_prompt_erase": True,
        "new_install_improv_wait_time": 0,
        "builds": [{
            "chipFamily": "ESP32-S3",
            "serialType": "uart",
            "improv": False,
            "parts": [{"path": "factory.bin", "offset": 0}],
        }],
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {factory_path} ({len(image)} bytes)")
    print(f"SHA-256: {hashlib.sha256(image).hexdigest()}")


if __name__ == "__main__":
    main()
