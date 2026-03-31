# ROI Viewer

A single-page tool for loading PNG images and picking rectangular regions of interest (ROI) via mouse or manual coordinate entry — built with [NiceGUI](https://nicegui.io/) and [Pillow](https://python-pillow.org/).

---

## Features

- **PNG loading** — drag & drop a file onto the upload area, or click to open a file picker; non-PNG files are rejected
- **Image display** — the image fills the right column with a crosshair cursor ready for drawing
- **Mouse-based rectangle drawing** — click-drag-release on the image to define a region; the overlay is updated in real time during the drag
- **Manual coordinate input** — two switchable modes:
  - **XYWH** — top-left corner (X, Y) + Width + Height
  - **XYXY** — first corner (X1, Y1) + opposite corner (X2, Y2)
- **Mode synchronisation** — switching modes never changes the selection; the alternate representation is always shown read-only beneath the inputs
- **Coordinate normalisation** — any drag direction is handled correctly (`x = min(x0,x1)`, `w = abs(x1−x0)`, etc.)
- **Apply / Reset** — *Apply* validates and redraws; *Reset* clears the selection while the image stays loaded
- **Load another image** — replaces the current image and resets the selection

---

## Screenshots

**Idle state — no image loaded**

<img src="https://github.com/user-attachments/assets/464c333b-a2ac-42ef-af7e-936ff8e0d1ea">

**Image loaded — rectangle drawn via Apply (XYWH mode)**

<img src="https://github.com/user-attachments/assets/067ef9f5-4709-4006-b6ba-851cdd643f00">

**XYXY mode — auto-converted, derived XYWH shown below**

<img src="https://github.com/user-attachments/assets/254b02e5-7408-4916-9765-79a3d297468f">

---

## Dependencies

| Package | Purpose |
|---------|---------|
| [nicegui](https://nicegui.io/) | Web-based UI framework (layout, inputs, interactive image, events) |
| [Pillow](https://python-pillow.org/) | PNG validation, image loading, dimension retrieval |

Python standard-library modules used: `base64`, `io`.

---

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/bizulk/roi_viewer.git
   cd roi_viewer
   ```

2. **Create and activate a virtual environment** (recommended)
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

---

## Running

```bash
python main.py
```

The app starts a local web server and opens automatically in your browser at <http://localhost:8080>.

---

## Usage

1. **Load a PNG** — drag & drop a `.png` file onto the upload area in the left panel, or click it to open a file picker.
2. **Draw a region** — click and drag on the image to draw a rectangle; the coordinates update live.
3. **Edit coordinates manually** — choose *XYWH* or *XYXY* mode, edit the fields, and press **Apply** (or hit Enter in any field).
4. **Reset** — click **Reset selection** to clear the rectangle without unloading the image.
5. **Load another image** — click the **Load another image** button to start over with a new file.
