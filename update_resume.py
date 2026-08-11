import os
import io
import re
import shutil
import zipfile
from pathlib import Path

MASTER = Path("master-resume.docx")
OUTPUT = Path("custom-resume.docx")


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
    shutil.copy2(MASTER, OUTPUT)

    data = OUTPUT.read_bytes()

    with zipfile.ZipFile(io.BytesIO(data), "r") as zin:
        xml = zin.read("word/document.xml")

        # Target the existing Backend skill text run.
        pattern = re.compile(
            rb'(<w:t[^>]*>Spring Boot • Spring Security • '
            rb'Spring Data JPA • Hibernate • REST APIs • JWT • '
            rb'Maven • Node\.js</w:t>)'
        )

        match = pattern.search(xml)

        if not match:
            raise RuntimeError("Backend skills section not found.")

        current = match.group(1).decode("utf-8")

        existing = {
            x.strip().casefold()
            for x in re.findall(r'>([^<]+)</w:t>', current)
            for x in x.split("•")
            if x.strip()
        }

        new_skills = [
            skill
            for skill in skills
            if skill.casefold() not in existing
        ]

        if not new_skills:
            print("No new skills.")
            return

        addition = " • " + " • ".join(new_skills)

        addition_xml = (
            addition
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

        replacement = match.group(1)[:-5] + addition_xml.encode() + b"</w:t>"

        new_xml = (
            xml[:match.start()]
            + replacement
            + xml[match.end():]
        )

        output = io.BytesIO()

        with zipfile.ZipFile(
            output,
            "w",
            zipfile.ZIP_DEFLATED
        ) as zout:

            for item in zin.infolist():
                content = (
                    new_xml
                    if item.filename == "word/document.xml"
                    else zin.read(item.filename)
                )

                zout.writestr(item, content)

    OUTPUT.write_bytes(output.getvalue())

    print("Added:", ", ".join(new_skills))


if __name__ == "__main__":
    skills = get_skills()

    if not skills:
        raise RuntimeError("No skills supplied.")

    update_resume(skills)
