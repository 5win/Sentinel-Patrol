#!/usr/bin/env python3
"""Convert a ROS map (pgm + yaml) into PNG + JS config for the dashboard.

Usage:
    python3 prepare_map.py ~/waffle_map.yaml

Outputs (into public/ alongside this script by default):
    public/map.png         - map image the dashboard draws as background
    public/map_config.js   - resolution, origin, width, height as a JS global

Vite copies everything in public/ verbatim into dist/, so after `npm run build`:
    dist/map.png
    dist/map_config.js

Requires: PyYAML, Pillow  (pip install pyyaml pillow)
"""

import argparse
import os
from pathlib import Path

import yaml
from PIL import Image


def main():
    default_out = Path(__file__).parent / "public"

    parser = argparse.ArgumentParser()
    parser.add_argument("map_yaml", help="Path to ROS map yaml (e.g. ~/waffle_map.yaml)")
    parser.add_argument(
        "--out-dir",
        default=str(default_out),
        help="Output directory (default: public/ alongside this script)",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    yaml_path = os.path.expanduser(args.map_yaml)
    with open(yaml_path) as f:
        meta = yaml.safe_load(f)

    img_rel = meta["image"]
    img_path = (
        img_rel if os.path.isabs(img_rel)
        else os.path.join(os.path.dirname(yaml_path), img_rel)
    )

    resolution = float(meta["resolution"])
    origin = meta["origin"]

    img = Image.open(img_path)
    width, height = img.size

    png_out = out_dir / "map.png"
    img.save(png_out)

    config_out = out_dir / "map_config.js"
    with open(config_out, "w") as f:
        f.write(
            "window.MAP_CONFIG = {\n"
            "  image: 'map.png',\n"
            f"  resolution: {resolution},\n"
            f"  origin: {{ x: {origin[0]}, y: {origin[1]} }},\n"
            f"  width: {width},\n"
            f"  height: {height},\n"
            "};\n"
        )

    print(f"Wrote {png_out}")
    print(f"Wrote {config_out}")
    print(f"  resolution={resolution}  origin=({origin[0]}, {origin[1]})  size={width}x{height}")


if __name__ == "__main__":
    main()
