#!/usr/bin/env python3
"""
Create a multi-layer draw.io file from a manifest.json.

Supported element types:
- image: embeds PNG/JPG/SVG as data URI
- text: native draw.io text/shape object
- rect: native rounded/rect shape
- connector: native line/polyline connector using absolute points

Usage:
    python scripts/create_drawio_from_manifest.py manifest.json output.drawio
"""

from __future__ import annotations

import base64
import json
import mimetypes
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape


def data_uri(path: Path) -> str:
    mime, _ = mimetypes.guess_type(path.name)
    if mime is None:
        if path.suffix.lower() == ".svg":
            mime = "image/svg+xml"
        else:
            mime = "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def cell(parent_el: ET.Element, **attrs) -> ET.Element:
    return ET.SubElement(parent_el, "mxCell", {k: str(v) for k, v in attrs.items() if v is not None})


def geom(parent_el: ET.Element, **attrs) -> ET.Element:
    return ET.SubElement(parent_el, "mxGeometry", {k: str(v) for k, v in attrs.items() if v is not None})


def add_layer(root: ET.Element, layer_id: str, name: str) -> None:
    cell(root, id=layer_id, value=name, parent="0")


def add_image(root: ET.Element, element: dict, parent_id: str, assets_dir: Path) -> None:
    file_path = assets_dir / element["file"]
    uri = data_uri(file_path)
    style = element.get("style") or "shape=image;verticalLabelPosition=bottom;verticalAlign=top;imageAspect=0;aspect=fixed;"
    style = style.rstrip(";") + f";image={uri};"
    if element.get("locked"):
        style += "locked=1;"
    c = cell(root, id=element["id"], value="", style=style, vertex="1", parent=parent_id)
    geom(c, x=element.get("x", 0), y=element.get("y", 0), width=element.get("w", 100), height=element.get("h", 100), **{"as": "geometry"})


def add_text(root: ET.Element, element: dict, parent_id: str) -> None:
    default_style = "rounded=0;whiteSpace=wrap;html=1;strokeColor=none;fillColor=none;fontSize=20;align=center;verticalAlign=middle;"
    style = element.get("style") or default_style
    c = cell(root, id=element["id"], value=escape(element.get("text", "")), style=style, vertex="1", parent=parent_id)
    geom(c, x=element.get("x", 0), y=element.get("y", 0), width=element.get("w", 100), height=element.get("h", 40), **{"as": "geometry"})


def add_rect(root: ET.Element, element: dict, parent_id: str) -> None:
    default_style = "rounded=1;whiteSpace=wrap;html=1;strokeColor=#1B4DFF;fillColor=#FFFFFF;fontColor=#1B4DFF;fontSize=20;align=center;verticalAlign=middle;"
    style = element.get("style") or default_style
    c = cell(root, id=element["id"], value=escape(element.get("text", "")), style=style, vertex="1", parent=parent_id)
    geom(c, x=element.get("x", 0), y=element.get("y", 0), width=element.get("w", 100), height=element.get("h", 40), **{"as": "geometry"})


def add_shape(root: ET.Element, element: dict, parent_id: str) -> None:
    default_style = "rounded=0;whiteSpace=wrap;html=1;strokeColor=#333333;fillColor=#FFFFFF;fontColor=#222222;fontSize=20;align=center;verticalAlign=middle;"
    style = element.get("style") or default_style
    shape = element.get("shape")
    if shape and "shape=" not in style:
        style = style.rstrip(";") + f";shape={shape};"
    c = cell(root, id=element["id"], value=escape(element.get("text", "")), style=style, vertex="1", parent=parent_id)
    geom(c, x=element.get("x", 0), y=element.get("y", 0), width=element.get("w", 100), height=element.get("h", 40), **{"as": "geometry"})


def add_connector(root: ET.Element, element: dict, parent_id: str) -> None:
    points = element.get("points", [])
    if len(points) < 2:
        raise ValueError(f"connector {element.get('id')} requires at least two points")
    style = element.get("style") or "endArrow=classic;html=1;rounded=1;strokeColor=#1B4DFF;strokeWidth=2;"
    c = cell(root, id=element["id"], value="", style=style, edge="1", parent=parent_id)
    g = geom(c, relative="1", **{"as": "geometry"})
    ET.SubElement(g, "mxPoint", {"x": str(points[0][0]), "y": str(points[0][1]), "as": "sourcePoint"})
    ET.SubElement(g, "mxPoint", {"x": str(points[-1][0]), "y": str(points[-1][1]), "as": "targetPoint"})
    if len(points) > 2:
        arr = ET.SubElement(g, "Array", {"as": "points"})
        for x, y in points[1:-1]:
            ET.SubElement(arr, "mxPoint", {"x": str(x), "y": str(y)})


def build_drawio(manifest_path: Path, output_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    canvas = manifest.get("canvas", {"width": 1600, "height": 900})
    assets_dir = (manifest_path.parent / manifest.get("assets_dir", "assets")).resolve()

    mxfile = ET.Element("mxfile", {
        "host": "app.diagrams.net",
        "agent": "ChatGPT image-to-drawio skill",
        "version": "24.7.17",
        "type": "device",
    })
    diagram = ET.SubElement(mxfile, "diagram", {"name": "Page-1", "id": "page-1"})
    model = ET.SubElement(diagram, "mxGraphModel", {
        "dx": str(canvas.get("width", 1600)),
        "dy": str(canvas.get("height", 900)),
        "grid": "1",
        "gridSize": "10",
        "guides": "1",
        "tooltips": "1",
        "connect": "1",
        "arrows": "1",
        "fold": "1",
        "page": "1",
        "pageScale": "1",
        "pageWidth": str(canvas.get("width", 1600)),
        "pageHeight": str(canvas.get("height", 900)),
        "math": "0",
        "shadow": "0",
    })
    root = ET.SubElement(model, "root")
    cell(root, id="0")
    cell(root, id="1", parent="0")

    layer_map = {}
    for idx, name in enumerate(manifest.get("layers", []), start=1):
        layer_id = f"layer_{idx:02d}_{name}"
        layer_map[name] = layer_id
        add_layer(root, layer_id, name)

    for element in manifest.get("elements", []):
        layer_name = element.get("layer", "1")
        parent_id = layer_map.get(layer_name, "1")
        etype = element.get("type")
        if etype == "image":
            add_image(root, element, parent_id, assets_dir)
        elif etype == "text":
            add_text(root, element, parent_id)
        elif etype == "rect":
            add_rect(root, element, parent_id)
        elif etype in {"shape", "ellipse", "rhombus"}:
            if etype == "ellipse" and "shape" not in element:
                element = {**element, "shape": "ellipse"}
            elif etype == "rhombus" and "shape" not in element:
                element = {**element, "shape": "rhombus"}
            add_shape(root, element, parent_id)
        elif etype in {"connector", "line"}:
            add_connector(root, element, parent_id)
        else:
            raise ValueError(f"unsupported element type: {etype}")

    ET.indent(mxfile, space="  ")
    output_path.write_text(ET.tostring(mxfile, encoding="unicode"), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_drawio_from_manifest.py manifest.json output.drawio", file=sys.stderr)
        sys.exit(1)
    build_drawio(Path(sys.argv[1]), Path(sys.argv[2]))
