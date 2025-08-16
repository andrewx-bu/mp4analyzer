#!/usr/bin/env python3
"""Command-line interface for MP4 Analyzer."""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List

from . import parse_mp4_boxes, generate_movie_info, format_box_tree


class Colors:
    """ANSI color codes."""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    BOLD = '\033[1m'
    END = '\033[0m'


def _colorize(text: str, color: str, use_color: bool) -> str:
    """Apply color if enabled."""
    return f"{color}{text}{Colors.END}" if use_color else text


def _box_to_dict(box) -> Dict[str, Any]:
    """Convert MP4Box to dictionary for JSON serialization."""
    return {
        "type": box.type,
        "size": box.size,
        "offset": box.offset,
        "properties": box.properties(),
        "children": [_box_to_dict(child) for child in box.children],
    }


def _format_properties(properties: Dict[str, Any], indent: int = 0, use_color: bool = False, expand: bool = False) -> List[str]:
    """Format box properties for display."""
    lines = []
    prefix = "  " * (indent + 1)

    for key, value in properties.items():
        if key == "box_name":
            continue

        key_colored = _colorize(key, Colors.CYAN, use_color)

        if isinstance(value, list) and len(value) > 0:
            if expand or len(value) <= 5:
                value_str = ', '.join(map(str, value))
                if len(value_str) > 80:  # Split long arrays
                    lines.append(f"{prefix}{key_colored}: [")
                    items = [str(x) for x in value]
                    line = f"{prefix}    "
                    for i, item in enumerate(items):
                        if len(line + item) > 120:
                            lines.append(line.rstrip(', ') + ',')
                            line = f"{prefix}    {item}"
                        else:
                            line += f"{item}, " if i < len(items) - 1 else item
                    lines.append(line + "]")
                else:
                    lines.append(f"{prefix}{key_colored}: [{value_str}]")
            else:
                display_value = f"[{', '.join(map(str, value[:5]))}...] ({len(value)} items)"
                lines.append(f"{prefix}{key_colored}: {display_value}")
        elif isinstance(value, bytes):
            if expand or len(value) <= 16:
                hex_str = value.hex() if value else "(empty)"
                if len(hex_str) > 80:  # Split long hex data
                    lines.append(f"{prefix}{key_colored}: ")
                    for i in range(0, len(hex_str), 64):
                        chunk = hex_str[i:i+64]
                        lines.append(f"{prefix}    {chunk}")
                else:
                    lines.append(f"{prefix}{key_colored}: {hex_str}")
            else:
                display_value = f"{value[:16].hex()}... ({len(value)} bytes)"
                lines.append(f"{prefix}{key_colored}: {display_value}")
        else:
            display_value = str(value)
            if len(display_value) > 80:  # Split long strings
                lines.append(f"{prefix}{key_colored}: ")
                for i in range(0, len(display_value), 80):
                    chunk = display_value[i:i+80]
                    lines.append(f"{prefix}    {chunk}")
            else:
                lines.append(f"{prefix}{key_colored}: {display_value}")

    return lines


def _format_box_tree_visual(boxes, indent: int = 0, is_last: List[bool] = None, show_properties: bool = True, use_color: bool = False, expand: bool = False) -> List[str]:
    """Format box tree with visual hierarchy."""
    lines = []
    if is_last is None:
        is_last = []

    for i, box in enumerate(boxes):
        is_final = i == len(boxes) - 1

        # Build tree characters
        tree_chars = ""
        for last in is_last:
            tree_chars += "    " if last else "│   "

        tree_chars += "└── " if is_final else "├── "

        # Box info with colors
        box_type = _colorize(box.type, Colors.BOLD + Colors.BLUE, use_color)
        size_info = _colorize(f"size={box.size:,}", Colors.GREEN, use_color)
        offset_info = _colorize(f"offset={box.offset:,}", Colors.GRAY, use_color)

        box_line = f"{tree_chars}{box_type} ({size_info}, {offset_info})"
        if hasattr(box, "__class__") and box.__class__.__name__ != "MP4Box":
            class_name = _colorize(f"[{box.__class__.__name__}]", Colors.PURPLE, use_color)
            box_line += f" {class_name}"

        lines.append(box_line)

        # Show properties if requested
        if show_properties:
            props = box.properties()
            filtered_props = {k: v for k, v in props.items() if k not in {"size", "start", "box_name"}}

            if filtered_props:
                prop_prefix = ""
                for last in is_last:
                    prop_prefix += "    " if last else "│   "
                prop_prefix += "    " if is_final else "│   "

                for j, line in enumerate(_format_properties(filtered_props, 0, use_color, expand)):
                    lines.append(f"{prop_prefix}{line.strip()}")

        # Process children
        if box.children:
            lines.extend(_format_box_tree_visual(
                box.children,
                indent + 1,
                is_last + [is_final],
                show_properties,
                use_color,
                expand
            ))

    return lines


def _output_stdout(file_path: str, boxes, movie_info: str, detailed: bool = False, use_color: bool = False, expand: bool = False) -> None:
    """Output analysis to stdout in human-readable format."""
    title = f"MP4 Analysis: {Path(file_path).name}"
    title_colored = _colorize(title, Colors.BOLD + Colors.WHITE, use_color)
    print(title_colored.center(60 if not use_color else 80))
    print(_colorize("=" * 60, Colors.GRAY, use_color))

    # Movie info with colors
    movie_lines = movie_info.splitlines()
    for line in movie_lines:
        if ":" in line and use_color:
            key, val = line.split(":", 1)
            line = f"{_colorize(key, Colors.YELLOW, use_color)}:{val}"
        print(line)
    print()

    # Box structure
    print(_colorize("Box Structure:", Colors.BOLD + Colors.WHITE, use_color))
    print(_colorize("-" * 30, Colors.GRAY, use_color))

    lines = _format_box_tree_visual(boxes, show_properties=detailed, use_color=use_color, expand=expand)
    for line in lines:
        print(line)


def _output_summary(file_path: str, boxes, use_color: bool = False) -> None:
    """Output a concise summary of the MP4 file."""
    title = _colorize(f"MP4 Summary: {Path(file_path).name}", Colors.BOLD + Colors.WHITE, use_color)
    print(title)
    print(_colorize("=" * 40, Colors.GRAY, use_color))

    # Count box types
    box_counts = {}
    total_size = 0

    def count_boxes(box_list):
        nonlocal total_size
        for box in box_list:
            box_counts[box.type] = box_counts.get(box.type, 0) + 1
            total_size += box.size
            count_boxes(box.children)

    count_boxes(boxes)

    # Show summary with colors
    print(f"{_colorize('Total file size:', Colors.YELLOW, use_color)} {total_size:,} bytes")
    print(f"{_colorize('Top-level boxes:', Colors.YELLOW, use_color)} {len(boxes)}")
    print(f"{_colorize('Total box count:', Colors.YELLOW, use_color)} {sum(box_counts.values())}")
    print()

    print(_colorize("Box type counts:", Colors.BOLD, use_color))
    for box_type, count in sorted(box_counts.items()):
        box_colored = _colorize(box_type, Colors.BLUE, use_color)
        print(f"  {box_colored}: {count}")


def _output_json(file_path: str, boxes, movie_info: str, json_path: str = None) -> None:
    """Output analysis as JSON."""
    data = {
        "file_path": file_path,
        "movie_info": movie_info,
        "boxes": [_box_to_dict(box) for box in boxes],
    }

    json_str = json.dumps(data, indent=2, default=str)

    if json_path:
        with open(json_path, "w") as f:
            f.write(json_str)
        print(f"JSON output saved to: {json_path}")
    else:
        print(json_str)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze MP4 files and display metadata information",
        prog="mp4analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mp4analyzer video.mp4                    # Basic analysis with color
  mp4analyzer -d video.mp4                 # Detailed view with box properties
  mp4analyzer -s video.mp4                 # Quick summary
  mp4analyzer -e video.mp4                 # Expand all arrays/matrices
  mp4analyzer --no-color video.mp4         # Disable colors
  mp4analyzer -o json video.mp4            # JSON output
  mp4analyzer -j output.json video.mp4     # Save JSON to file
        """,
    )

    parser.add_argument("file", help="MP4 file to analyze")

    parser.add_argument("-o", "--output", choices=["stdout", "json"], default="stdout", help="Output format (default: stdout)")
    parser.add_argument("-d", "--detailed", action="store_true", help="Show detailed box properties and internal fields")
    parser.add_argument("-s", "--summary", action="store_true", help="Show concise summary instead of full analysis")
    parser.add_argument("-e", "--expand", action="store_true", help="Expand all arrays and large data structures")
    parser.add_argument("-c", "--color", action="store_true", default=True, help="Enable colored output (default: True)")
    parser.add_argument("--no-color", action="store_false", dest="color", help="Disable colored output")
    parser.add_argument("-j", "--json-path", help="Path to save JSON output")

    args = parser.parse_args()

    # Auto-detect color support
    use_color = args.color and (os.getenv("NO_COLOR") is None) and (sys.stdout.isatty() or os.getenv("FORCE_COLOR"))

    # Validate file exists
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    if not file_path.is_file():
        print(f"Error: Not a file: {file_path}", file=sys.stderr)
        sys.exit(1)

    try:
        # Parse the MP4 file
        boxes = parse_mp4_boxes(str(file_path))

        if not boxes:
            print("Error: No MP4 boxes found in file", file=sys.stderr)
            sys.exit(1)

        # Output based on format and options
        if args.output == "json":
            json_path = args.json_path or f"{file_path.stem}.mp4analyzer.json"
            movie_info = generate_movie_info(str(file_path), boxes)
            _output_json(str(file_path), boxes, movie_info, json_path)
        else:
            if args.summary:
                _output_summary(str(file_path), boxes, use_color)
            else:
                movie_info = generate_movie_info(str(file_path), boxes)
                _output_stdout(str(file_path), boxes, movie_info, args.detailed, use_color, args.expand)

        # Save JSON if json_path specified regardless of output format
        if args.json_path and args.output != "json":
            movie_info = generate_movie_info(str(file_path), boxes)
            _output_json(str(file_path), boxes, movie_info, args.json_path)

    except Exception as e:
        print(f"Error analyzing file: {e}", file=sys.stderr)
        if args.detailed:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
