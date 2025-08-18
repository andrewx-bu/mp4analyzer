# MP4 Analyzer
![CI](https://github.com/andrewx-bu/mp4analyzer/actions/workflows/ci.yml/badge.svg)
![Release](https://github.com/andrewx-bu/mp4analyzer/actions/workflows/release.yml/badge.svg)
![PyPI - Version](https://img.shields.io/pypi/v/mp4analyzer?label=PyPI&color=blue "https://pypi.org/project/mp4analyzer/")
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg "https://opensource.org/licenses/MIT")

Tool for analyzing MP4 files, providing both command-line box parsing and GUI-based frame-level analysis.

| CLI | GUI |
| --- | --- |
| <img src="https://github.com/andrewx-bu/mp4analyzer/blob/main/images/cli.png?raw=true" width="400" alt="CLI"> | <img src="https://github.com/andrewx-bu/mp4analyzer/blob/main/images/gui.png?raw=true" width="800" alt="GUI"> |

## Features

### CLI Tool
- Parse and display MP4 box structure
- Extract metadata and technical information (e.g. duration, bitrate, codec info, track details)
- Supports output to JSON. No external dependencies needed

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
usage: mp4analyzer [-h] [-o {stdout,json}] [-d] [-s] [-e] [-c | --no-color] [-j JSON_PATH] file

Analyze MP4 files and display metadata information

positional arguments:
  file                  MP4 file to analyze

options:
  -h, --help            show this help message and exit
  -o {stdout,json}, --output {stdout,json}
                        Output format (default: stdout)
  -d, --detailed        Show detailed box properties and internal fields
  -s, --summary         Show concise summary instead of full analysis
  -e, --expand          Expand all arrays and large data structures
  -c, --color           Enable colored output (default: True)
      --no-color        Disable colored output
  -j JSON_PATH, --json-path JSON_PATH
                        Path to save JSON output. If specified, JSON will be saved even if
                        output format is not json.

Examples:
  mp4analyzer video.mp4                    # Basic analysis with color
  mp4analyzer -d video.mp4                 # Detailed view with box properties
  mp4analyzer -s video.mp4                 # Quick summary
  mp4analyzer -e -d video.mp4              # Expand arrays/matrices in details
  mp4analyzer --no-color video.mp4         # Disable ANSI colors
  mp4analyzer -o json video.mp4            # JSON to stdout
  mp4analyzer -j output.json video.mp4     # Save JSON to file (in addition to stdout)
```

### GUI Application
Download and run the executable from GitHub [Releases](https://github.com/andrewx-bu/mp4analyzer/releases). The application will not run without FFmpeg. Works best with files < 100 MB.

## Supported Box Types

### ISO Base Media (MP4)
`ac4`, `av01`, `av1C`, `avc1`, `avcC`, `btrt`, `colr`, `ctts`, `dac4`, `dinf`, `dref`, `edts`, `elst`, `esds`, `free`, `ftyp`, `hdlr`,
`hev1`, `hvcC`, `iods`, `mdat`, `mdhd`, `mdia`, `mehd`, `meta`, `mfhd`, `mfra`, `mfro`, `minf`, `moof`, `moov`, `mp4a`, `mvex`, `mvhd`,
`pasp`, `sbgp`, `sdtp`, `sgpd`, `smhd`, `stbl`, `stco`, `stsc`, `stsd`, `stss`, `stsz`, `stts`, `tfdt`, `tfhd`, `tfra`, `tkhd`, `traf`,
`trak`, `tref`, `trex`, `trun`, `udta`, `url `, `vmhd`

### QuickTime Extensions
`chpl`, `gmhd`, `gmin`, `text` (gmhd), `ilst`, `data`, `text` (sample entry), `fiel`

### TODO
Add more boxes (e.g., VP9 codec, fragmented MP4, etc.)

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

### Built With
![Technologies](https://go-skill-icons.vercel.app/api/icons?i=python,qt,ffmpeg,pytest,githubactions,&perline=5&theme=dark)
