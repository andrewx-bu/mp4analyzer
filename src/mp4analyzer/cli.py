#!/usr/bin/env python3
"""Command-line interface for MP4 Analyzer."""

import argparse
import json
import sys
import os
import textwrap
from pathlib import Path
from typing import Dict, Any, List

from . import parse_mp4_boxes, generate_movie_info


class Colors:
    """ANSI color codes for terminal output."""

    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"
    BOLD = "\033[1m"
    END = "\033[0m"


def _colorize(text: str, color: str, use_color: bool) -> str:
    """Wrap text with ANSI codes if color enabled."""
    return f"{color}{text}{Colors.END}" if use_color else text


def _box_to_dict(box) -> Dict[str, Any]:
    """Convert MP4Box tree to dict (for JSON export)."""
    return {
        "type": box.type,
        "size": box.size,
        "offset": box.offset,
        "properties": box.properties(),
        "children": [_box_to_dict(child) for child in box.children],
    }


def _format_properties(
    properties: Dict[str, Any],
    indent: int = 0,
    use_color: bool = False,
    expand: bool = False,
) -> List[str]:
    """Pretty-print box properties with optional expand/color."""
    lines = []
    prefix = "  " * (indent + 1)

    for key, value in properties.items():
        if key == "box_name":
            continue
        key_colored = _colorize(key, Colors.CYAN, use_color)

        if isinstance(value, list) and value:
            # Handle arrays (truncate or expand fully)
            if expand or len(value) <= 5:
                # If list contains nested structures, pretty-print using JSON
                if any(isinstance(v, (list, dict)) for v in value):
                    json_lines = json.dumps(value, indent=4).splitlines()
                    lines.append(f"{prefix}{key_colored}: {json_lines[0]}")
                    for json_line in json_lines[1:]:
                        lines.append(f"{prefix}{json_line}")
                else:
                    value_str = ", ".join(map(str, value))
                    if len(value_str) > 80:  # wrap long lists
                        lines.append(f"{prefix}{key_colored}: [")
                        items = [f"{x}," for x in value]
                        line = f"{prefix}    "
                        for item in items:
                            if len(line + item) > 120:
                                lines.append(line.rstrip())
                                line = f"{prefix}    {item} "
                            else:
                                line += f"{item} "
                        lines.append(line.rstrip())
                        lines.append(f"{prefix}]")
                    else:
                        lines.append(f"{prefix}{key_colored}: [{value_str}]")
            else:
                lines.append(
                    f"{prefix}{key_colored}: "
                    f"[{', '.join(map(str, value[:5]))}...] ({len(value)} items)"
                )
        elif isinstance(value, dict):
            json_lines = json.dumps(value, indent=4).splitlines()
            lines.append(f"{prefix}{key_colored}: {json_lines[0]}")
            for json_line in json_lines[1:]:
                lines.append(f"{prefix}{json_line}")
        elif isinstance(value, bytes):
            # Handle byte fields as hex grouped into 8-char chunks
            if expand or len(value) <= 16:
                if not value:
                    lines.append(f"{prefix}{key_colored}: (empty)")
                else:
                    hex_str = value.hex()
                    groups = [hex_str[i:i+8] for i in range(0, len(hex_str), 8)]

                    # Print first line with key
                    first = " ".join(groups[:8])
                    lines.append(f"{prefix}{key_colored}: {first}")

                    # Continuation lines aligned to first hex value position
                    cont_prefix = f"{prefix}{' ' * len(key)}  "

                    # Remaining lines
                    for i in range(8, len(groups), 8):
                        chunk = " ".join(groups[i:i+8])
                        lines.append(f"{cont_prefix}{chunk}")
            else:
                preview = value[:16].hex()
                groups = [preview[i:i+8] for i in range(0, len(preview), 8)]
                lines.append(
                    f"{prefix}{key_colored}: {' '.join(groups)}... ({len(value)} bytes)"
                )
        else:
            # Fallback: string conversion, wrapping without breaking words
            display_value = str(value)
            if len(display_value) > 80:
                wrapped = textwrap.wrap(
                    display_value, width=80, break_long_words=False, break_on_hyphens=False
                )
                lines.append(f"{prefix}{key_colored}: {wrapped[0]}")
                for segment in wrapped[1:]:
                    lines.append(f"{prefix}    {segment}")
            else:
                lines.append(f"{prefix}{key_colored}: {display_value}")

    return lines


def _format_box_tree_visual(
    boxes,
    indent: int = 0,
    is_last: List[bool] = None,
    show_properties: bool = True,
    use_color: bool = False,
    expand: bool = False,
) -> List[str]:
    """Draw tree view of MP4 box hierarchy."""
    lines = []
    if is_last is None:
        is_last = []

    for i, box in enumerate(boxes):
        is_final = i == len(boxes) - 1

        # Build branch/line prefixes
        tree_chars = "".join("    " if last else "│   " for last in is_last)
        tree_chars += "└── " if is_final else "├── "

        # Box info
        box_type = _colorize(box.type, Colors.BOLD + Colors.BLUE, use_color)
        size_info = _colorize(f"size={box.size:,}", Colors.GREEN, use_color)
        offset_info = _colorize(f"offset={box.offset:,}", Colors.GRAY, use_color)
        box_line = f"{tree_chars}{box_type} ({size_info}, {offset_info})"

        # Add subclass name if not plain MP4Box
        if box.__class__.__name__ != "MP4Box":
            class_name = _colorize(
                f"[{box.__class__.__name__}]", Colors.PURPLE, use_color
            )
            box_line += f" {class_name}"
        lines.append(box_line)

        # Show box properties
        if show_properties:
            props = {
                k: v
                for k, v in box.properties().items()
                if k not in {"size", "start", "box_name"}
            }
            if props:
                prop_prefix = "".join("    " if last else "│   " for last in is_last)
                prop_prefix += "    " if is_final else "│   "
                for line in _format_properties(props, 0, use_color, expand):
                    lines.append(f"{prop_prefix}{line.rstrip()}")

        # Recurse into children
        if box.children:
            lines.extend(
                _format_box_tree_visual(
                    box.children,
                    indent + 1,
                    is_last + [is_final],
                    show_properties,
                    use_color,
                    expand,
                )
            )

    return lines


def _output_stdout(
    file_path: str,
    boxes,
    movie_info: str,
    detailed: bool = False,
    use_color: bool = False,
    expand: bool = False,
) -> None:
    """Print analysis to stdout with tree and metadata."""
    title = f"MP4 Analysis: {Path(file_path).name}"
    print(
        _colorize(title, Colors.BOLD + Colors.WHITE, use_color).center(
            60 if not use_color else 80
        )
    )
    print(_colorize("=" * 60, Colors.GRAY, use_color))

    # Print metadata info
    for line in movie_info.splitlines():
        if ":" in line and use_color:
            key, val = line.split(":", 1)
            line = f"{_colorize(key, Colors.YELLOW, use_color)}:{val}"
        print(line)
    print()

    # Print box hierarchy
    print(_colorize("Box Structure:", Colors.BOLD + Colors.WHITE, use_color))
    print(_colorize("-" * 30, Colors.GRAY, use_color))
    for line in _format_box_tree_visual(
        boxes, show_properties=detailed, use_color=use_color, expand=expand
    ):
        print(line)


def _output_summary(file_path: str, boxes, use_color: bool = False) -> None:
    """Print short file summary (counts, size, box stats)."""
    print(
        _colorize(
            f"MP4 Summary: {Path(file_path).name}",
            Colors.BOLD + Colors.WHITE,
            use_color,
        )
    )
    print(_colorize("=" * 40, Colors.GRAY, use_color))

    box_counts, total_size = {}, 0

    def count_boxes(box_list):
        nonlocal total_size
        for box in box_list:
            box_counts[box.type] = box_counts.get(box.type, 0) + 1
            total_size += box.size
            count_boxes(box.children)

    count_boxes(boxes)

    # Stats
    print(
        f"{_colorize('Total file size:', Colors.YELLOW, use_color)} {total_size:,} bytes"
    )
    print(f"{_colorize('Top-level boxes:', Colors.YELLOW, use_color)} {len(boxes)}")
    print(
        f"{_colorize('Total box count:', Colors.YELLOW, use_color)} {sum(box_counts.values())}\n"
    )

    print(_colorize("Box type counts:", Colors.BOLD, use_color))
    for box_type, count in sorted(box_counts.items()):
        print(f"  {_colorize(box_type, Colors.BLUE, use_color)}: {count}")


def _output_json(file_path: str, boxes, movie_info: str, json_path: str = None) -> None:
    """Write analysis as JSON (stdout or file)."""
    data = {
        "file_path": file_path,
        "movie_info": movie_info,
        "boxes": [_box_to_dict(b) for b in boxes],
    }
    json_str = json.dumps(data, indent=2, default=str)

    if json_path:
        with open(json_path, "w") as f:
            f.write(json_str)
        print(f"JSON output saved to: {json_path}")
    else:
        print(json_str)


def main():
    """CLI entry point: parse args, analyze file, print output."""
    parser = argparse.ArgumentParser(
        description="Analyze MP4 files and display metadata",
        prog="mp4analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  mp4analyzer video.mp4             # Basic analysis
  mp4analyzer -d video.mp4          # Detailed with box properties
  mp4analyzer -s video.mp4          # Summary only
  mp4analyzer -e video.mp4          # Expand arrays
  mp4analyzer --no-color video.mp4  # Disable colors
  mp4analyzer -o json video.mp4     # JSON output
  mp4analyzer -j out.json video.mp4 # Save JSON to file
        """,
    )

    # CLI options
    parser.add_argument("file", help="MP4 file to analyze")
    parser.add_argument(
        "-o",
        "--output",
        choices=["stdout", "json"],
        default="stdout",
        help="Output format",
    )
    parser.add_argument(
        "-d", "--detailed", action="store_true", help="Show detailed box properties"
    )
    parser.add_argument(
        "-s", "--summary", action="store_true", help="Show concise summary"
    )
    parser.add_argument(
        "-e", "--expand", action="store_true", help="Expand arrays/matrices fully"
    )
    parser.add_argument(
        "-c", "--color", action="store_true", default=True, help="Enable colored output"
    )
    parser.add_argument(
        "--no-color", action="store_false", dest="color", help="Disable colored output"
    )
    parser.add_argument("-j", "--json-path", help="Path to save JSON")

    args = parser.parse_args()

    # Detect if colors should be used
    use_color = (
        args.color
        and (os.getenv("NO_COLOR") is None)
        and (sys.stdout.isatty() or os.getenv("FORCE_COLOR"))
    )

    # Validate file exists
    file_path = Path(args.file)
    if not file_path.exists() or not file_path.is_file():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    try:
        boxes = parse_mp4_boxes(str(file_path))
        if not boxes:
            print("Error: No MP4 boxes found", file=sys.stderr)
            sys.exit(1)

        # Output mode
        if args.output == "json":
            movie_info = generate_movie_info(str(file_path), boxes)
            _output_json(
                str(file_path),
                boxes,
                movie_info,
                args.json_path or f"{file_path.stem}.mp4analyzer.json",
            )
        else:
            if args.summary:
                _output_summary(str(file_path), boxes, use_color)
            else:
                movie_info = generate_movie_info(str(file_path), boxes)
                _output_stdout(
                    str(file_path),
                    boxes,
                    movie_info,
                    args.detailed,
                    use_color,
                    args.expand,
                )

        # Also save JSON if requested in non-json mode
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
