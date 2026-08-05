#!/usr/bin/env python3
"""Regenerate the OfficeCLI DOCX inspection fixture.

Valid, schema-clean Word document with body-level tables (merged cells),
an inline PNG image, and plain paragraphs. Deterministic output (fixed zip
timestamps). No user or restricted content.

Run from the repo root:
    python skills/ppt-master/fixtures/officecli/rebuild_docx_source.py
"""

import base64
import io
import zipfile
from pathlib import Path

from PIL import Image

OUT = Path(__file__).resolve().parent / "docx_source.docx"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"


def _run(text: str) -> str:
    return f"<w:r><w:t xml:space='preserve'>{text}</w:t></w:r>"


def _cell(text: str) -> str:
    return f"<w:tc><w:p>{_run(text)}</w:p></w:tc>"


def _table(rows: list[list[str]]) -> str:
    ncols = max(len(r) for r in rows)
    grid = "".join(f"<w:gridCol w:w='1700'/>" for _ in range(ncols))
    trs = ""
    for row in rows:
        cells = "".join(_cell(c) for c in row)
        trs += f"<w:tr>{cells}</w:tr>"
    # OfficeCLI's schema validator requires w:tblPr before w:tblGrid.
    return f"<w:tbl><w:tblPr/><w:tblGrid>{grid}</w:tblGrid>{trs}</w:tbl>"


def _make_png() -> bytes:
    img = Image.new("RGB", (200, 120), (92, 160, 92))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def main() -> int:
    png = _make_png()

    tables = (
        _table([["指标 A", "指标 B", "2026 Q1"], ["12.4%", "8.1%", "持平"], ["备注", "合计", "42"]])
        + _table([["产品", "Q1", "Q2"], ["Widget", "120", "135"]])
    )
    body = (
        f"<w:p>{_run('OfficeCLI DOCX inspection fixture')}</w:p>"
        f"<w:p>{_run('Two tables, one inline image, plain paragraphs.')}</w:p>"
        + tables
        + f"<w:p><w:r><w:drawing><wp:inline xmlns:wp='http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing' "
        f"xmlns:a='http://schemas.openxmlformats.org/drawingml/2006/main' distT='0' distB='0' distL='0' distR='0'>"
        f"<wp:extent cx='2286000' cy='1371600'/><wp:docPr id='1' name='Picture 1'/>"
        f"<a:graphic><a:graphicData uri='http://schemas.openxmlformats.org/drawingml/2006/picture'>"
        f"<pic:pic xmlns:pic='http://schemas.openxmlformats.org/drawingml/2006/picture'>"
        f"<pic:nvPicPr><pic:cNvPr id='1' name='inline.png'/><pic:cNvPicPr/></pic:nvPicPr>"
        f"<pic:blipFill><a:blip r:embed='rId1'/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>"
        f"<pic:spPr><a:xfrm><a:off x='0' y='0'/><a:ext cx='2286000' cy='1371600'/></a:xfrm>"
        f"<a:prstGeom prst='rect'><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic>"
        f"</wp:inline></w:drawing></w:r></w:p>"
        f"<w:p>{_run('Footer paragraph.')}</w:p>"
    )
    document = (
        f"<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
        f"<w:document xmlns:w='{W}' xmlns:r='{R}'><w:body>{body}"
        f"<w:sectPr><w:pgSz w:w='11906' w:h='16838'/></w:sectPr></w:body></w:document>"
    )
    rels = (
        f"<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
        f"<Relationships xmlns='{REL_NS}'>"
        f"<Relationship Id='rId1' Type='{R}/image' Target='media/image1.png'/></Relationships>"
    )
    content_types = (
        f"<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
        f"<Types xmlns='{CT_NS}'>"
        f"<Default Extension='rels' ContentType='application/vnd.openxmlformats-package.relationships+xml'/>"
        f"<Default Extension='xml' ContentType='application/xml'/>"
        f"<Default Extension='png' ContentType='image/png'/>"
        f"<Override PartName='/word/document.xml' "
        f"ContentType='application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml'/>"
        f"</Types>"
    )
    root_rels = (
        f"<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
        f"<Relationships xmlns='{REL_NS}'>"
        f"<Relationship Id='rId1' Type='{R}/officeDocument' Target='word/document.xml'/></Relationships>"
    )

    parts = {
        "[Content_Types].xml": content_types.encode("utf-8"),
        "_rels/.rels": root_rels.encode("utf-8"),
        "word/document.xml": document.encode("utf-8"),
        "word/_rels/document.xml.rels": rels.encode("utf-8"),
        "word/media/image1.png": png,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(parts):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, parts[name])
    print(f"Written {OUT}")
    print("  Tables: 2, image: 1, paragraphs: 4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
