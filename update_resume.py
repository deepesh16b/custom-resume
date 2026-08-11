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

    # Always start from the untouched master
    shutil.copy2(MASTER, OUTPUT)

    data = OUTPUT.read_bytes()

    with zipfile.ZipFile(io.BytesIO(data), "r") as zin:

        document_xml = zin.read("word/document.xml").decode("utf-8")

        # Find the existing Backend skills text.
        pattern = re.compile(
            r'(<w:t[^>]*>'
            r'[^<]*Spring Boot • Spring Security • '
            r'Spring Data JPA • Hibernate • REST APIs • JWT • '
            r'Maven • Node\.js'
            r'</w:t>)'
        )

        match = pattern.search(document_xml)

        if not match:
            raise RuntimeError(
                "Could not find the Backend skills section."
            )

        current = match.group(1)

        # Extract current skills
        text_only = re.sub(r'<[^>]+>', '', current)

        existing = {
            x.strip().casefold()
            for x in text_only.split("•")
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

        addition = " • " + " • ".join(new_skills)

        # Add only the new text before </w:t>
        replacement = (
            match.group(1)[:-6]
            + addition
            + "</w:t>"
        )

        document_xml = (
            document_xml[:match.start()]
            + replacement
            + document_xml[match.end():]
        )

        updated_xml = document_xml.encode("utf-8")

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
