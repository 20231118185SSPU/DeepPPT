#!/usr/bin/env python3
"""Regenerate the complex DOCX fidelity fixture (vMerge/gridSpan/sym/image).

stdlib-only (zipfile + XML strings). Run from the repo root:
    python3 skills/ppt-master/fixtures/docx_complex/rebuild_make_docx.py
"""
import base64
import zipfile
from pathlib import Path

OUT = Path(__file__).resolve().parent / "complex_v2.docx"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def run(t):
    return f'<w:r><w:t xml:space="preserve">{t}</w:t></w:r>'


def sym_run(font, code):
    return (f'<w:r><w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}"/></w:rPr>'
            f'<w:sym w:font="{font}" w:char="{code:04X}"/></w:r>')


def vmerge(text=None, restart=False):
    val = ' w:val="restart"' if restart else ""
    body = f"<w:p>{run(text)}</w:p>" if text else "<w:p/>"
    return f"<w:tc><w:tcPr><w:vMerge{val}/></w:tcPr>{body}</w:tc>"


def cell(text, span=None):
    pr = f"<w:tcPr><w:gridSpan w:val='{span}'/></w:tcPr>" if span else ""
    return f"<w:tc>{pr}<w:p>{run(text)}</w:p></w:tc>"


def tbl_xml(rows, ncols):
    grid = "".join(f'<w:gridCol w:w="1700"/>' for _ in range(ncols))
    trs = "".join(f"<w:tr>{''.join(cells)}</w:tr>" for cells in rows)
    return f'<w:tbl><w:tblGrid>{grid}</w:tblGrid>{trs}</w:tbl>'


def main() -> int:
    # 表 1：4 列 = [vMerge 指标A][vMerge 指标B][gridSpan2 数值][gridSpan2 数值]
    t1 = [
        [vmerge("指标 A", restart=True), vmerge("指标 B", restart=True), cell("2026 Q1", span=2)],
        [vmerge(), vmerge(), cell("12.4%", span=2)],
        [cell("2025 Q4"), cell("8.1%"), cell("持平", span=2)],
    ]
    # 表 2：圈号 sym（双字体）+ 多段落 cell
    t2 = [
        [f"<w:tc><w:p>{sym_run('Wingdings 2', 0xF06A)}{run(' 区域一')}</w:p></w:tc>",
         f"<w:tc><w:p>{sym_run('Wingdings 2', 0xF06B)}{run(' 区域二')}</w:p></w:tc>",
         f"<w:tc><w:p>{sym_run('Wingdings', 0xF081)}{run(' 区域三')}</w:p></w:tc>"],
        [("<w:tc><w:p>多段落</w:p><w:p>第二段内容</w:p></w:tc>"), cell("42"), cell("说明文字")],
    ]
    img_rid = "rIdImg"
    body = (
        f'<w:p>{run("复杂输入合成文档 v2：合法合并结构 + 圈号 + 图片")}</w:p>'
        f'<w:p>{tbl_xml(t1, 4)}</w:p>'
        f'<w:p>{tbl_xml(t2, 3)}</w:p>'
        f'<w:p><w:r><w:drawing><wp:inline '
        f'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        f'distT="0" distB="0" distL="0" distR="0"><wp:extent cx="914400" cy="457200"/>'
        f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        f'<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:blipFill><a:blip r:embed="{img_rid}"/></pic:blipFill><pic:spPr/>'
        f'</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'
    )
    document = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                f'<w:document xmlns:w="{W}" xmlns:r="{R}"><w:body>{body}<w:sectPr/></w:body></w:document>')
    content_types = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Default Extension="png" ContentType="image/png"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>'''
    rels = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            f'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>\n'
            f'</Relationships>')
    doc_rels = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                f'<Relationship Id="{img_rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png"/>\n'
                f'</Relationships>')
    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )
    with zipfile.ZipFile(OUT, "w") as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", document)
        z.writestr("word/media/image1.png", png)
        z.writestr("word/_rels/document.xml.rels", doc_rels)
    print(f"written {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
