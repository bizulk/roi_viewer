#!/usr/bin/env python3
"""ROI Viewer – PNG image viewer with rectangular region-of-interest selection.

Usage:
    python main.py

Controls:
    • Drag & drop a PNG onto the upload area, or click to pick a file.
    • Click-drag on the image to draw a rectangle.
    • Edit coordinates manually (XYWH or XYXY mode) and press Apply.
    • Reset clears the selection; Load another image resets everything.
"""

import base64
import io

from nicegui import events, ui
from PIL import Image, UnidentifiedImageError

# ---------------------------------------------------------------------------
# Application state (single-user desktop tool)
# ---------------------------------------------------------------------------

_state: dict = {
    "image_source": None,   # data-URL string (base64-encoded PNG)
    "image_width": 0,
    "image_height": 0,
    "filename": "",
    "sel": None,            # {"x", "y", "w", "h"} in image pixels, or None
    "drawing": False,
    "start_x": 0.0,
    "start_y": 0.0,
    "mode": "XYWH",        # "XYWH" | "XYXY"
}

# References to UI elements, populated during page construction
_ui: dict = {}

# ---------------------------------------------------------------------------
# Pure helper functions
# ---------------------------------------------------------------------------


def _norm_rect(x0: float, y0: float, x1: float, y1: float) -> dict:
    """Return a normalised {x, y, w, h} rectangle from any two corners."""
    return {
        "x": int(min(x0, x1)),
        "y": int(min(y0, y1)),
        "w": int(abs(x1 - x0)),
        "h": int(abs(y1 - y0)),
    }


def _sel_to_xyxy(sel: dict) -> tuple[int, int, int, int]:
    """Convert XYWH selection dict to (x1, y1, x2, y2) tuple."""
    return sel["x"], sel["y"], sel["x"] + sel["w"], sel["y"] + sel["h"]


def _svg(sel: dict | None) -> str:
    """Return SVG markup for the rectangle overlay (empty string = no rect)."""
    if sel is None or sel["w"] == 0 or sel["h"] == 0:
        return ""
    x, y, w, h = sel["x"], sel["y"], sel["w"], sel["h"]
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
        'fill="rgba(255,0,0,0.15)" stroke="red" stroke-width="2" '
        'stroke-dasharray="6,3"/>'
    )


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# UI update helpers
# ---------------------------------------------------------------------------


def _refresh_inputs() -> None:
    """Push current selection values into the coordinate input fields."""
    sel = _state["sel"] or {"x": 0, "y": 0, "w": 0, "h": 0}
    mode = _state["mode"]

    if mode == "XYWH":
        _ui["inp_x"].value = str(sel["x"])
        _ui["inp_y"].value = str(sel["y"])
        _ui["inp_w"].value = str(sel["w"])
        _ui["inp_h"].value = str(sel["h"])
        x1, y1, x2, y2 = _sel_to_xyxy(sel)
        _ui["derived"].set_text(
            f"XYXY  →  x1={x1}  y1={y1}  x2={x2}  y2={y2}"
        )
    else:
        x1, y1, x2, y2 = _sel_to_xyxy(sel)
        _ui["inp_x1"].value = str(x1)
        _ui["inp_y1"].value = str(y1)
        _ui["inp_x2"].value = str(x2)
        _ui["inp_y2"].value = str(y2)
        _ui["derived"].set_text(
            f'XYWH  →  x={sel["x"]}  y={sel["y"]}  '
            f'w={sel["w"]}  h={sel["h"]}'
        )


def _refresh_svg() -> None:
    """Re-render the SVG rectangle overlay on the interactive image."""
    _ui["iimg"].set_content(_svg(_state["sel"]))


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------


async def _on_upload(e: events.UploadEventArguments) -> None:
    """Handle a file upload event (drag-drop or file picker)."""
    filename: str = e.file.name
    if not filename.lower().endswith(".png"):
        ui.notify("Only PNG files are supported.", type="negative")
        return

    raw = await e.file.read()
    try:
        img = Image.open(io.BytesIO(raw))
        if img.format != "PNG":
            raise ValueError("Not PNG")
        width, height = img.size
    except (UnidentifiedImageError, ValueError):
        ui.notify(
            "Failed to load image – make sure it is a valid PNG file.",
            type="negative",
        )
        return

    _state["image_width"] = width
    _state["image_height"] = height
    _state["filename"] = filename
    _state["sel"] = None
    _state["drawing"] = False
    b64 = base64.b64encode(raw).decode()
    _state["image_source"] = f"data:image/png;base64,{b64}"

    _show_image()


def _show_image() -> None:
    """Switch the UI to the image-loaded state."""
    _ui["idle_panel"].set_visibility(False)
    _ui["idle_hint"].set_visibility(False)

    _ui["iimg"].set_source(_state["image_source"])
    _ui["iimg"].set_content("")
    _ui["iimg"].set_visibility(True)

    _ui["fname"].set_text(
        f'{_state["filename"]}  '
        f'({_state["image_width"]} × {_state["image_height"]} px)'
    )
    _ui["controls_panel"].set_visibility(True)
    _refresh_inputs()


def _load_another() -> None:
    """Reset to idle state so the user can load a new image."""
    _state["image_source"] = None
    _state["sel"] = None
    _state["drawing"] = False

    _ui["controls_panel"].set_visibility(False)
    _ui["iimg"].set_visibility(False)
    _ui["idle_hint"].set_visibility(True)
    _ui["idle_panel"].set_visibility(True)


def _apply() -> None:
    """Read coordinate fields and update the selection + overlay."""
    try:
        mode = _state["mode"]
        if mode == "XYWH":
            x = int(_ui["inp_x"].value)
            y = int(_ui["inp_y"].value)
            w = int(_ui["inp_w"].value)
            h = int(_ui["inp_h"].value)
            _state["sel"] = _norm_rect(x, y, x + w, y + h)
        else:
            x1 = int(_ui["inp_x1"].value)
            y1 = int(_ui["inp_y1"].value)
            x2 = int(_ui["inp_x2"].value)
            y2 = int(_ui["inp_y2"].value)
            _state["sel"] = _norm_rect(x1, y1, x2, y2)
    except (ValueError, TypeError):
        ui.notify(
            "Invalid coordinates – please enter integer values.",
            type="warning",
        )
        return

    _refresh_svg()
    _refresh_inputs()


def _reset() -> None:
    """Clear the current selection (image stays loaded)."""
    _state["sel"] = None
    _refresh_svg()
    _refresh_inputs()


def _on_mode(value: str) -> None:
    """Handle coordinate mode toggle (XYWH / XYXY)."""
    _state["mode"] = value
    _ui["xywh_panel"].set_visibility(value == "XYWH")
    _ui["xyxy_panel"].set_visibility(value == "XYXY")
    _refresh_inputs()


def _on_mouse(e: events.MouseEventArguments) -> None:
    """Handle mouse events on the interactive image for drawing a rectangle."""
    if not _state["image_width"]:
        return

    ix = _clamp(e.image_x, 0, _state["image_width"])
    iy = _clamp(e.image_y, 0, _state["image_height"])

    if e.type == "mousedown":
        _state["drawing"] = True
        _state["start_x"] = ix
        _state["start_y"] = iy
        _state["sel"] = _norm_rect(ix, iy, ix, iy)

    elif e.type == "mousemove" and _state["drawing"]:
        _state["sel"] = _norm_rect(
            _state["start_x"], _state["start_y"], ix, iy
        )
        _refresh_svg()
        _refresh_inputs()

    elif e.type == "mouseup" and _state["drawing"]:
        _state["drawing"] = False
        _state["sel"] = _norm_rect(
            _state["start_x"], _state["start_y"], ix, iy
        )
        _refresh_svg()
        _refresh_inputs()


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------


@ui.page("/")
def index() -> None:
    ui.page_title("ROI Viewer")

    # ── Top bar ──────────────────────────────────────────────────────────────
    with ui.header().classes("items-center bg-primary text-white q-px-md q-py-sm"):
        ui.icon("crop_free").classes("q-mr-sm")
        ui.label("ROI Viewer").classes("text-h6 text-weight-bold")

    # ── Main two-column layout ────────────────────────────────────────────────
    with ui.row().classes("w-full items-start no-wrap q-pa-md gap-6"):

        # ── Left column – control panel ──────────────────────────────────────
        with ui.column().classes("gap-4").style("min-width:270px; width:270px"):

            # · Upload card (visible in idle state)
            with ui.card().classes("w-full q-pa-sm") as idle_panel:
                _ui["idle_panel"] = idle_panel
                ui.label("Load Image").classes(
                    "text-subtitle1 text-weight-bold q-mb-xs"
                )
                (
                    ui.upload(
                        label="Drop PNG here or click to choose",
                        on_upload=_on_upload,
                        auto_upload=True,
                        max_files=1,
                    )
                    .props('accept=".png,image/png" flat bordered')
                    .classes("w-full")
                )

            # · Controls card (visible after image is loaded)
            with ui.card().classes("w-full q-pa-sm") as controls_panel:
                _ui["controls_panel"] = controls_panel
                controls_panel.set_visibility(False)

                # File info row
                _ui["fname"] = ui.label("").classes(
                    "text-caption text-grey-7 q-mb-xs"
                )

                # Load another image
                (
                    ui.button(
                        "Load another image",
                        on_click=_load_another,
                        icon="folder_open",
                    )
                    .props("flat color=primary dense")
                    .classes("w-full q-mb-sm")
                )

                ui.separator()

                # Coordinate mode selector
                ui.label("Coordinate Mode").classes(
                    "text-subtitle2 text-weight-bold q-mt-sm"
                )
                (
                    ui.select(
                        ["XYWH", "XYXY"],
                        value="XYWH",
                        on_change=lambda e: _on_mode(e.value),
                    )
                    .classes("w-full q-mb-sm")
                    .props("dense outlined")
                )

                ui.separator()

                # XYWH input group
                with ui.column().classes("gap-1 w-full q-mt-sm") as xywh_panel:
                    _ui["xywh_panel"] = xywh_panel
                    ui.label("XYWH").classes("text-caption text-grey-6")
                    with ui.grid(columns=2).classes("w-full gap-2"):
                        _ui["inp_x"] = (
                            ui.input("X", value="0")
                            .props("type=number dense outlined")
                            .classes("w-full")
                        )
                        _ui["inp_y"] = (
                            ui.input("Y", value="0")
                            .props("type=number dense outlined")
                            .classes("w-full")
                        )
                        _ui["inp_w"] = (
                            ui.input("Width", value="0")
                            .props("type=number dense outlined")
                            .classes("w-full")
                        )
                        _ui["inp_h"] = (
                            ui.input("Height", value="0")
                            .props("type=number dense outlined")
                            .classes("w-full")
                        )
                    # Apply on Enter key for any XYWH field
                    for key in ("inp_x", "inp_y", "inp_w", "inp_h"):
                        _ui[key].on("keydown.enter", _apply)

                # XYXY input group
                with ui.column().classes("gap-1 w-full q-mt-sm") as xyxy_panel:
                    _ui["xyxy_panel"] = xyxy_panel
                    xyxy_panel.set_visibility(False)
                    ui.label("XYXY").classes("text-caption text-grey-6")
                    with ui.grid(columns=2).classes("w-full gap-2"):
                        _ui["inp_x1"] = (
                            ui.input("X1", value="0")
                            .props("type=number dense outlined")
                            .classes("w-full")
                        )
                        _ui["inp_y1"] = (
                            ui.input("Y1", value="0")
                            .props("type=number dense outlined")
                            .classes("w-full")
                        )
                        _ui["inp_x2"] = (
                            ui.input("X2", value="0")
                            .props("type=number dense outlined")
                            .classes("w-full")
                        )
                        _ui["inp_y2"] = (
                            ui.input("Y2", value="0")
                            .props("type=number dense outlined")
                            .classes("w-full")
                        )
                    # Apply on Enter key for any XYXY field
                    for key in ("inp_x1", "inp_y1", "inp_x2", "inp_y2"):
                        _ui[key].on("keydown.enter", _apply)

                ui.separator()

                # Action buttons
                ui.label("Actions").classes(
                    "text-subtitle2 text-weight-bold q-mt-sm"
                )
                with ui.row().classes("gap-2 q-mt-xs"):
                    ui.button("Apply", on_click=_apply, icon="check").props(
                        "color=primary dense"
                    )
                    ui.button(
                        "Reset selection", on_click=_reset, icon="clear"
                    ).props("flat color=negative dense")

                ui.separator()

                # Read-only alternate-mode display
                _ui["derived"] = ui.label("").classes(
                    "text-caption text-grey-6 q-mt-xs"
                )

        # ── Right column – image area ────────────────────────────────────────
        with ui.column().classes("flex-grow items-center justify-center").style(
            "min-height:400px"
        ):
            # Placeholder shown when no image is loaded
            with ui.column().classes(
                "items-center justify-center gap-3"
            ) as idle_hint:
                _ui["idle_hint"] = idle_hint
                ui.icon("image", size="6rem").classes("text-grey-4")
                ui.label("No image loaded").classes("text-h6 text-grey-5")
                ui.label(
                    "Load a PNG file using the panel on the left"
                ).classes("text-caption text-grey-4")

            # Interactive image (hidden until a file is loaded)
            _ui["iimg"] = (
                ui.interactive_image(
                    source="",
                    on_mouse=_on_mouse,
                    events=["mousedown", "mousemove", "mouseup"],
                    cross=False,
                    sanitize=False,
                )
                .classes("max-w-full shadow-3")
                .style("cursor:crosshair")
            )
            _ui["iimg"].set_visibility(False)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="ROI Viewer", port=8080, reload=False)
