# MP4 Analyzer

## Overview
A desktop tool for inspecting MP4 containers that contain H.264 video streams.

## Core Features So Far
- **Box layout viewer** – displays the hierarchical MP4 box (atom) tree with each box's type, size, and file offset.
- **Frame timeline** – renders a bar graph of frame sizes and types, and lets users step through and view decoded frames.
- **Basic metadata panel** – shows summary information about the video using FFprobe.

## Goals
1. Parse inner fields for more box types and show detailed metadata
2. Enhance frame timeline with PTS, decode order, and reference frames when hovering over bars
3. Improve decoding performance or move heavy operations to a C++ module using libav?
4. **Stretch goal:** overlay macroblocks and motion vectors on the video view.