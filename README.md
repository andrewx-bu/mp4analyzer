# MP4 Analyzer

Tool for analyzing MP4 files, providing both command-line box parsing and GUI-based frame-level analysis.

| CLI | GUI |
| --- | --- |
| <img src="images/cli.png" width="400" alt="CLI"> | <img src="images/gui.png" width="800" alt="GUI"> |

## Features

### CLI Tool
- Parse and display MP4 box structure
- Extract metadata and technical information (e.g. duration, bitrate, codec info, track details)
- Supports output to JSON

### GUI Application
- Frame-by-frame video analysis with timeline visualization
- Per-frame details: type (I/P/B), byte size, timestamp, and decode vs presentation order
- Requires FFmpeg for video decoding

## Installation and Usage

### CLI Tool
```bash
pip install mp4analyzer
```

### CLI Help
```
usage: mp4analyzer [-h] [-o {stdout,json}] [-d] [-s] [-j JSON_PATH] file

Analyze MP4 files and display metadata information

positional arguments:
  file                  MP4 file to analyze

options:
  -h, --help            show this help message and exit
  -o {stdout,json}, --output {stdout,json}
                        Output format (default: stdout)
  -d, --detailed        Show detailed box properties and internal fields
  -s, --summary         Show concise summary instead of full analysis
  -j JSON_PATH, --json-path JSON_PATH
                        Path to save JSON output. If specified, JSON will be saved even if output format is not json

Examples:
  mp4analyzer video.mp4                    # Basic analysis
  mp4analyzer -d video.mp4                 # Detailed view with box properties
  mp4analyzer -s video.mp4                 # Quick summary
  mp4analyzer -o json video.mp4            # JSON output
  mp4analyzer -j output.json video.mp4     # Save JSON to file
```

### GUI Application
Download and run the executable from GitHub [Releases](https://github.com/andrewx-bu/mp4analyzer/releases). The application will not run without FFmpeg.

## Supported MP4 Boxes

Currently parsed box types: `ftyp`, `mvhd`, `tkhd`, `mdhd`, `iods`, `moov`, `trak`, `free`, `mdat`, `edts`, `elst`, `hdlr`, `minf`

Additional containers and leaf boxes are recognized but not fully parsed yet.

## Development

```bash
# Setup
uv sync --extra dev

# Run tests
uv run pytest

# Build GUI app
uv run python build_exe.py

# Build CLI package
uv build
```
