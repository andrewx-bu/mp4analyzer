#!/usr/bin/env python3
"""Command-line interface for MP4 Analyzer."""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

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


def _output_stdout(file_path: str, boxes, movie_info: str) -> None:
    """Output analysis to stdout in human-readable format."""
    print(f"MP4 Analysis: {file_path}")
    print("=" * 50)
    print()

    # Movie info
    print(movie_info)
    print()

    # Box tree
    print("Box Structure:")
    print("-" * 20)
    for box in boxes:
        lines = format_box_tree(box)
        for line in lines:
            print(line)


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

        # Generate movie info
        movie_info = generate_movie_info(str(file_path), boxes)

        # Output based on format
        if args.output == "stdout":
            _output_stdout(str(file_path), boxes, movie_info)
        elif args.output == "json":
            # Auto-generate JSON path if not provided
            json_path = args.json_path
            if not json_path:
                json_path = f"{file_path.stem}.mp4analyzer.json"
            _output_json(str(file_path), boxes, movie_info, json_path)

        # Save JSON if json_path specified regardless of output format
        if args.json_path and args.output != "json":
            _output_json(str(file_path), boxes, movie_info, args.json_path)

    except Exception as e:
        print(f"Error analyzing file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
