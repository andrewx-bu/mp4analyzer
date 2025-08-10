#!/usr/bin/env python3
"""Command-line interface for MP4 Analyzer."""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

from . import parse_mp4_boxes, generate_movie_info, format_box_tree


def _box_to_dict(box) -> Dict[str, Any]:
    """Convert MP4Box to dictionary for JSON serialization."""
    return {
        "type": box.type,
        "size": box.size,
        "offset": box.offset,
        "properties": box.properties(),
        "children": [_box_to_dict(child) for child in box.children],
    }


def _format_properties(properties: Dict[str, Any], indent: int = 0) -> List[str]:
    """Format box properties for display."""
    lines = []
    prefix = "  " * (indent + 1)

    for key, value in properties.items():
        if key == "box_name":
            continue  # Skip internal field

        if isinstance(value, list) and len(value) > 0:
            if len(value) > 5:  # Truncate long lists
                display_value = (
                    f"[{', '.join(map(str, value[:5]))}...] ({len(value)} items)"
                )
            else:
                display_value = f"[{', '.join(map(str, value))}]"
        elif isinstance(value, bytes):
            if len(value) > 16:
                display_value = f"{value[:16].hex()}... ({len(value)} bytes)"
            else:
                display_value = value.hex() if value else "(empty)"
        else:
            display_value = str(value)

        lines.append(f"{prefix}{key}: {display_value}")

    return lines


def _format_box_tree_detailed(
    box, indent: int = 0, show_properties: bool = True
) -> List[str]:
    """Format box tree with optional property details."""
    lines = []
    prefix = "  " * indent

    # Main box line
    box_line = f"{prefix}{box.type} (size={box.size:,}, offset={box.offset:,})"
    if hasattr(box, "__class__") and box.__class__.__name__ != "MP4Box":
        box_line += f" [{box.__class__.__name__}]"
    lines.append(box_line)

    # Show properties if requested and available
    if show_properties:
        props = box.properties()
        # Filter out basic properties already shown
        filtered_props = {
            k: v for k, v in props.items() if k not in {"size", "start", "box_name"}
        }

        if filtered_props:
            lines.extend(_format_properties(filtered_props, indent))

    # Process children
    for child in box.children:
        lines.extend(_format_box_tree_detailed(child, indent + 1, show_properties))

    return lines


def _output_stdout(
    file_path: str, boxes, movie_info: str, detailed: bool = False
) -> None:
    """Output analysis to stdout in human-readable format."""
    title = f"MP4 Analysis: {Path(file_path).name}"
    print(title.center(60))
    print("=" * 60)

    # Movie info
    movie_lines = movie_info.splitlines()
    for line in movie_lines:
        print(line)
    print()

    # Box structure
    print("Box Structure:")
    print("-" * 30)

    for i, box in enumerate(boxes):
        if detailed:
            lines = _format_box_tree_detailed(box, show_properties=True)
        else:
            lines = format_box_tree(box)

        for line in lines:
            print(line)

        # Add spacing between top-level boxes


def _output_summary(file_path: str, boxes) -> None:
    """Output a concise summary of the MP4 file."""
    print(f"MP4 Summary: {Path(file_path).name}")
    print("=" * 40)

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

    # Show summary
    print(f"Total file size: {total_size:,} bytes")
    print(f"Top-level boxes: {len(boxes)}")
    print(f"Total box count: {sum(box_counts.values())}")
    print()

    print("Box type counts:")
    for box_type, count in sorted(box_counts.items()):
        print(f"  {box_type}: {count}")


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
  mp4analyzer video.mp4                    # Basic analysis
  mp4analyzer -d video.mp4                 # Detailed view with box properties  
  mp4analyzer -s video.mp4                 # Quick summary
  mp4analyzer -o json video.mp4            # JSON output
  mp4analyzer -j output.json video.mp4     # Save JSON to file
        """,
    )

    parser.add_argument("file", help="MP4 file to analyze")

    parser.add_argument(
        "-o",
        "--output",
        choices=["stdout", "json"],
        default="stdout",
        help="Output format (default: stdout)",
    )

    parser.add_argument(
        "-d",
        "--detailed",
        action="store_true",
        help="Show detailed box properties and internal fields",
    )

    parser.add_argument(
        "-s",
        "--summary",
        action="store_true",
        help="Show concise summary instead of full analysis",
    )

    parser.add_argument(
        "-j",
        "--json-path",
        help="Path to save JSON output. If specified, JSON will be saved even if output format is not json",
    )

    args = parser.parse_args()

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
            # Auto-generate JSON path if not provided
            json_path = args.json_path
            if not json_path:
                json_path = f"{file_path.stem}.mp4analyzer.json"

            # Generate movie info for JSON
            movie_info = generate_movie_info(str(file_path), boxes)
            _output_json(str(file_path), boxes, movie_info, json_path)

        else:
            # stdout output
            if args.summary:
                _output_summary(str(file_path), boxes)
            else:
                # Generate movie info
                movie_info = generate_movie_info(str(file_path), boxes)
                _output_stdout(str(file_path), boxes, movie_info, args.detailed)

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
