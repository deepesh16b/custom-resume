import os
import io
import re
import html
import zipfile
from pathlib import Path

RESUME = Path("resume.docx")


def get_skills():
    raw = os.environ.get("SKILLS", "").strip()

    # Accept: Kafka, Redis, GraphQL
    # Also accepts: Kafka; Redis; GraphQL
    skills = [x.strip() for x in re.split(r"[,;\n]+", raw) if x.strip()]

    # Remove duplicates while preserving order
    result = []
    seen = set()

    for skill in skills:
        key = skill.casefold()
        if key not in seen:
            seen.add(key)
            result.append(skill)

    return result


def update_backend(skills):
    data = RESUME.read_bytes()

    with zipfile.ZipFile(io.BytesIO(data), "r") as zin:
        document_xml = zin.read("word/document.xml")

        # Find the Backend label and the text node containing its skills.
        # We modify ONLY that text node. All formatting XML remains untouched.
        pattern = re.compile(
            rb'(?:<w:t[^>]*>)([^<]*Spring Boot[^<]*Node\.js)(</w:t>)',
            re.DOTALL
        )

        match = pattern.search(document_xml)

        if not match:
            raise RuntimeError("Backend skills text was not found.")

        current_xml_text = match.group(1).decode("utf-8")
        current_text = html.unescape(current_xml_text)

        existing = {
            x.strip().casefold()
            for x in current_text.split("•")
            if x.strip()
        }

        new_skills = [
            skill for skill in skills
            if skill.casefold() not in existing
        ]

        if not new_skills:
            print("No new skills to add.")
            return False

        addition = " • " + " • ".join(new_skills)

        # XML-safe text
        addition_xml = (
            addition
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

        new_text = match.group(1) + addition_xml.encode("utf-8")

        updated_xml = (
            document_xml[:match.start(1)]
            + new_text
            + document_xml[match.end(1):]
        )

        # Rebuild the DOCX while keeping every other file unchanged.
        output = io.BytesIO()

        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                content = (
                    updated_xml
                    if item.filename == "word/document.xml"
                    else zin.read(item.filename)
                )
                zout.writestr(item, content)

    RESUME.write_bytes(output.getvalue())

    print("Added:", ", ".join(new_skills))
    return True


if __name__ == "__main__":
    skills = get_skills()

    if not skills:
        raise RuntimeError("No skills supplied.")

    update_backend(skills)
