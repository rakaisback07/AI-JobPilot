
import re
import fitz
from docx import Document
from io import BytesIO


SKILL_LIST = [
    "Python",
    "Java",
    "C++",
    "C",
    "SQL",
    "Machine Learning",
    "Artificial Intelligence",
    "Deep Learning",
    "NLP",
    "Natural Language Processing",
    "BERT",
    "PyTorch",
    "TensorFlow",
    "Scikit-learn",
    "Pandas",
    "NumPy",
    "Data Analysis",
    "Data Science",
    "Streamlit",
    "Flask",
    "Django",
    "HTML",
    "CSS",
    "JavaScript",
    "React",
    "Git",
    "GitHub",
    "Software Testing",
    "Manual Testing",
    "Automation Testing",
    "Selenium",
    "SDLC",
    "STLC",
    "Prompt Engineering",
    "Excel",
    "Power BI",
    "Cybersecurity",
    "Linux",
    "Networking"
]


def extract_resume_text(uploaded_file):
    filename = uploaded_file.name.lower()
    file_bytes = uploaded_file.getvalue()

    text = ""

    if filename.endswith(".pdf"):
        pdf = fitz.open(
            stream=file_bytes,
            filetype="pdf"
        )

        for page in pdf:
            text += page.get_text() + "\n"

        pdf.close()

    elif filename.endswith(".docx"):
        document = Document(BytesIO(file_bytes))

        for paragraph in document.paragraphs:
            text += paragraph.text + "\n"

        # Also read text inside tables
        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    text += cell.text + "\n"

    else:
        raise ValueError("Please upload a PDF or DOCX file.")

    return text.strip()


def extract_email(text):
    pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    emails = re.findall(pattern, text)

    return emails[0] if emails else "Not found"


def extract_phone(text):
    pattern = r"(?:\+91[\s-]?)?[6-9]\d{9}"
    numbers = re.findall(pattern, text)

    return numbers[0] if numbers else "Not found"


def extract_skills(text):
    found_skills = []
    text_lower = text.lower()

    for skill in SKILL_LIST:
        pattern = r"(?<!\w)" + re.escape(skill.lower()) + r"(?!\w)"

        if re.search(pattern, text_lower):
            found_skills.append(skill)

    return found_skills
