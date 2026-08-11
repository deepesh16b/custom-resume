import os
import io
import re
import shutil
import zipfile
from pathlib import Path
from lxml import etree

MASTER = Path("master-resume.docx")
OUTPUT = Path("custom-resume.docx")

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}


def get_skills():
    raw = os.environ.get("SKILLS", "").strip()

    skills = [
        x.strip()
        for x in re.split(r"[,;\n]+", raw)
        if x.strip()
    ]

    result = []
    seen = set()

    for skill in skills:
        key = skill.casefold()

        if key not in seen:
            seen.add(key)
            result.append(skill)

    return result


def update_resume(skills):

    # ALWAYS start from the untouched master
    shutil.copy2(MASTER, OUTPUT)

    data = OUTPUT.read_bytes()

    with zipfile.ZipFile(io.BytesIO(data), "r") as zin:

        document_xml = zin.read("word/document.xml")

        root = etree.fromstring(document_xml)

        backend_cell = None

        # Find the table row containing "Backend:"
        for row in root.xpath(".//w:tr", namespaces=NS):

            cells = row.xpath("./w:tc", namespaces=NS)

            if len(cells) < 2:
                continue

            first_cell_text = "".join(
                cells[0].xpath(".//w:t/text()", namespaces=NS)
            )

            if "Backend:" in first_cell_text:
                backend_cell = cells[1]
                break

        if backend_cell is None:
            raise RuntimeError(
                "Could not find Backend row in Skills table."
            )

        # Get all text nodes in the second cell
        text_nodes = backend_cell.xpath(
            ".//w:t",
            namespaces=NS
        )

        if not text_nodes:
            raise RuntimeError(
                "Backend cell contains no text."
            )

        current_text = "".join(
            node.text or ""
            for node in text_nodes
        )

        existing = {
            x.strip().casefold()
            for x in current_text.split("•")
            if x.strip()
        }

        new_skills = [
            skill
            for skill in skills
            if skill.casefold() not in existing
        ]

        if not new_skills:
            print("No new skills to add.")
            return

        # Add to the LAST text node.
        # This preserves the existing formatting XML.
        addition = " • " + " • ".join(new_skills)

        text_nodes[-1].text = (
            text_nodes[-1].text or ""
        ) + addition

        updated_xml = etree.tostring(
            root,
            xml_declaration=True,
            encoding="UTF-8",
            standalone=True
        )

        output = io.BytesIO()

        with zipfile.ZipFile(
            output,
            "w",
            zipfile.ZIP_DEFLATED
        ) as zout:

            for item in zin.infolist():

                if item.filename == "word/document.xml":
                    content = updated_xml
                else:
                    content = zin.read(item.filename)

                zout.writestr(item, content)

    OUTPUT.write_bytes(output.getvalue())

    print(
        "Created custom resume with:",
        ", ".join(new_skills)
    )


if __name__ == "__main__":

    skills = get_skills()

    if not skills:
        raise RuntimeError("No skills supplied.")

    update_resume(skills)
