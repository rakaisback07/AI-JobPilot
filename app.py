
import streamlit as st
import pandas as pd

from database.db import (
    initialize_database,
    insert_jobs,
    get_all_jobs,
    get_job_count,
    save_application,
    get_applications,
    update_application,
    get_application_count
)

from resume.parser import (
    extract_resume_text,
    extract_email,
    extract_phone,
    extract_skills
)

from models.bert_matcher import rank_jobs

from jobs.sample_jobs import sample_jobs
from jobs.job_fetcher import fetch_jobs


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="AI JobPilot",
    page_icon="🚀",
    layout="wide"
)


# --------------------------------------------------
# DATABASE INITIALIZATION
# --------------------------------------------------

initialize_database()

# Add sample jobs only when the database is empty.
if get_job_count() == 0:
    insert_jobs(sample_jobs)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

if "resume_skills" not in st.session_state:
    st.session_state.resume_skills = []

if "resume_email" not in st.session_state:
    st.session_state.resume_email = "Not found"

if "resume_phone" not in st.session_state:
    st.session_state.resume_phone = "Not found"

if "ranked_jobs" not in st.session_state:
    st.session_state.ranked_jobs = []


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def save_job(job_id):
    success = save_application(job_id)

    if success:
        st.success("Job saved to your application tracker.")
    else:
        st.info("This job is already saved.")


def show_job(job, show_score=False):
    with st.container(border=True):

        st.subheader(job.get("title", "Untitled"))

        st.write(
            f"**Company:** {job.get('company', 'Unknown')}"
        )

        st.write(
            f"**Location:** {job.get('location', 'Not specified')}"
        )

        st.write(
            f"**Job Type:** {job.get('job_type', 'Not specified')}"
        )

        st.write(
            f"**Work Mode:** {job.get('work_mode', 'Not specified')}"
        )

        st.write(
            f"**Experience:** {job.get('experience', 'Not specified')}"
        )

        if show_score:
            score = float(job.get("match_score", 0))

            st.write(f"**Semantic Match:** {score}%")
            st.progress(int(max(0, min(100, score))))

        with st.expander("View Job Description"):
            st.write(
                job.get("description", "No description available.")
            )

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "Save Job",
                key=f"save_{job['id']}"
            ):
                save_job(job["id"])

        with col2:
            apply_url = job.get("apply_url", "")

            if apply_url:
                st.link_button(
                    "View / Apply",
                    apply_url
                )


def generate_cover_letter(
    candidate_name,
    company,
    job_title,
    skills,
    resume_text
):
    skill_text = ", ".join(skills[:8]) if skills else "relevant technical skills"

    return f"""Dear Hiring Manager,

I am writing to express my interest in the {job_title} position at {company}.

My academic background and practical learning have helped me develop knowledge
in areas such as {skill_text}. I am interested in applying these skills to
real-world projects and contributing positively to your organisation.

Through my academic projects and training, I have developed an understanding
of technical problem-solving, learning new tools, and working with structured
tasks. I am enthusiastic about improving my capabilities and learning from
experienced professionals.

I would appreciate the opportunity to discuss how my background and skills
may align with your requirements.

Thank you for your time and consideration.

Sincerely,
{candidate_name}
"""


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.title("🚀 AI JobPilot")

st.sidebar.caption(
    "AI-powered Resume Analysis and Job Recommendation System"
)

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Resume Analyzer",
        "AI Job Matching",
        "Job Search",
        "Cover Letter",
        "Application Tracker"
    ]
)

st.sidebar.divider()

st.sidebar.caption("Powered by Streamlit, Sentence Transformers and SQLite")


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

if page == "Dashboard":

    st.title("🚀 AI JobPilot Dashboard")

    st.write(
        "Your AI-powered assistant for resume analysis, "
        "job recommendations and application tracking."
    )

    jobs = get_all_jobs()
    applications = get_application_count()

    col1, col2, col3 = st.columns(3)

    col1.metric("Available Jobs", len(jobs))
    col2.metric(
        "Resume Uploaded",
        "Yes" if st.session_state.resume_text else "No"
    )
    col3.metric("Saved Applications", applications)

    st.divider()

    st.subheader("Getting Started")

    st.markdown("""
    1. Open **Resume Analyzer** and upload your PDF or DOCX resume.
    2. Review the extracted email, phone number and skills.
    3. Open **AI Job Matching** to rank jobs based on your resume.
    4. Open **Job Search** to filter jobs or fetch available listings.
    5. Save relevant jobs and monitor them in **Application Tracker**.
    6. Use **Cover Letter** to create a basic editable draft.
    """)

    st.info(
        "The first AI matching operation may take some time because "
        "the transformer model needs to be downloaded and loaded."
    )


# --------------------------------------------------
# RESUME ANALYZER
# --------------------------------------------------

elif page == "Resume Analyzer":

    st.title("📄 Resume Analyzer")

    st.write(
        "Upload your resume to extract text, contact information "
        "and technical skills."
    )

    uploaded_file = st.file_uploader(
        "Upload your resume",
        type=["pdf", "docx"]
    )

    if uploaded_file is not None:

        if st.button("Analyze Resume", type="primary"):

            try:
                with st.spinner("Analyzing your resume..."):

                    resume_text = extract_resume_text(uploaded_file)

                    if not resume_text.strip():
                        st.error(
                            "No readable text was found. "
                            "Your PDF may be scanned or image-based."
                        )
                    else:
                        st.session_state.resume_text = resume_text
                        st.session_state.resume_email = extract_email(
                            resume_text
                        )
                        st.session_state.resume_phone = extract_phone(
                            resume_text
                        )
                        st.session_state.resume_skills = extract_skills(
                            resume_text
                        )

                        st.success("Resume analyzed successfully.")

            except Exception as error:
                st.error(f"Resume analysis failed: {error}")

    if st.session_state.resume_text:

        st.divider()
        st.subheader("Extracted Information")

        col1, col2 = st.columns(2)

        col1.write(
            f"**Email:** {st.session_state.resume_email}"
        )

        col2.write(
            f"**Phone:** {st.session_state.resume_phone}"
        )

        st.subheader("Detected Skills")

        if st.session_state.resume_skills:
            st.write(", ".join(st.session_state.resume_skills))
        else:
            st.warning(
                "No skills from the current keyword list were detected."
            )

        with st.expander("View Extracted Resume Text"):
            st.text_area(
                "Resume Content",
                st.session_state.resume_text,
                height=300
            )


# --------------------------------------------------
# AI JOB MATCHING
# --------------------------------------------------

elif page == "AI Job Matching":

    st.title("🤖 AI Job Matching")

    st.write(
        "Compare your resume with available job descriptions "
        "using a lightweight transformer model."
    )

    if not st.session_state.resume_text:

        st.warning(
            "Please upload and analyze your resume first."
        )

    else:

        if st.button("Find Matching Jobs", type="primary"):

            jobs = get_all_jobs()

            if not jobs:
                st.warning("No jobs are currently available.")

            else:
                try:
                    with st.spinner(
                        "Calculating semantic similarity..."
                    ):
                        results = rank_jobs(
                            st.session_state.resume_text,
                            jobs
                        )

                        st.session_state.ranked_jobs = results

                    st.success("Job matching completed.")

                except Exception as error:
                    st.error(f"Matching failed: {error}")

        results = st.session_state.ranked_jobs

        if results:

            st.subheader("Ranked Job Recommendations")

            for job in results:
                show_job(job, show_score=True)


# --------------------------------------------------
# JOB SEARCH
# --------------------------------------------------

elif page == "Job Search":

    st.title("🔍 Job Search")

    st.write(
        "Search the available job records and filter them "
        "according to your preferences."
    )

    col1, col2 = st.columns(2)

    with col1:
        country = st.selectbox(
            "Country",
            [
                "All",
                "India",
                "United States",
                "United Kingdom",
                "Canada",
                "Germany"
            ]
        )

        location = st.text_input(
            "City, State or Region",
            placeholder="Example: Delhi, Haryana, Noida"
        )

        role = st.text_input(
            "Job Role",
            placeholder="Example: Python Developer"
        )

    with col2:
        work_mode = st.selectbox(
            "Work Mode",
            ["All", "Remote", "Hybrid", "On-site"]
        )

        job_type = st.selectbox(
            "Job Type",
            [
                "All",
                "Full-time",
                "Part-time",
                "Internship",
                "Contract"
            ]
        )

        experience = st.selectbox(
            "Experience",
            [
                "All",
                "Fresher",
                "0-1 years",
                "1-3 years",
                "3-5 years"
            ]
        )

    if st.button("Search Jobs", type="primary"):

        jobs = get_all_jobs()
        filtered_jobs = []

        for job in jobs:

            if country != "All":
                if country.lower() not in (
                    job.get("country", "") or ""
                ).lower():
                    continue

            if location:
                searchable_location = (
                    job.get("location", "") or ""
                ).lower()

                if location.lower() not in searchable_location:
                    continue

            if role:
                searchable_role = (
                    job.get("title", "") or ""
                ).lower()

                if role.lower() not in searchable_role:
                    continue

            if work_mode != "All":
                if work_mode.lower() not in (
                    job.get("work_mode", "") or ""
                ).lower():
                    continue

            if job_type != "All":
                if job_type.lower() not in (
                    job.get("job_type", "") or ""
                ).lower():
                    continue

            if experience != "All":
                if experience.lower() not in (
                    job.get("experience", "") or ""
                ).lower():
                    continue

            filtered_jobs.append(job)

        st.session_state.search_results = filtered_jobs

    if "search_results" in st.session_state:

        results = st.session_state.search_results

        st.write(f"Found {len(results)} matching records.")

        if results:
            for job in results:
                show_job(job)
        else:
            st.info("No jobs matched your selected filters.")

    st.divider()

    st.subheader("Fetch Live Job Listings")

    st.caption(
        "This optional feature requests job listings from the "
        "configured external job-board APIs."
    )

    search_keyword = st.text_input(
        "Search keyword for remote jobs",
        placeholder="Example: Python, Data Analyst, AI"
    )

    if st.button("Fetch Jobs from APIs"):

        try:
            with st.spinner("Fetching job listings..."):

                live_jobs = fetch_jobs(search_keyword)

                if live_jobs:
                    insert_jobs(live_jobs)
                    st.success(
                        f"Fetched and saved {len(live_jobs)} job records."
                    )
                    st.info(
                        "Return to Search Jobs and click Search Jobs "
                        "to view the updated records."
                    )
                else:
                    st.warning(
                        "No job records were returned. "
                        "Check your internet connection or try later."
                    )

        except Exception as error:
            st.error(f"Job fetching failed: {error}")


# --------------------------------------------------
# COVER LETTER
# --------------------------------------------------

elif page == "Cover Letter":

    st.title("✉️ Cover Letter Assistant")

    st.write(
        "Create a basic cover-letter draft using your details "
        "and the job information."
    )

    if not st.session_state.resume_text:
        st.warning(
            "Upload and analyze your resume first for a better draft."
        )

    candidate_name = st.text_input(
        "Your Name",
        placeholder="Enter your full name"
    )

    company = st.text_input(
        "Company Name",
        placeholder="Enter company name"
    )

    job_title = st.text_input(
        "Job Title",
        placeholder="Example: AI/ML Intern"
    )

    if st.button("Generate Cover Letter", type="primary"):

        if not candidate_name or not company or not job_title:
            st.warning(
                "Please enter your name, company and job title."
            )

        else:
            letter = generate_cover_letter(
                candidate_name,
                company,
                job_title,
                st.session_state.resume_skills,
                st.session_state.resume_text
            )

            st.session_state.generated_letter = letter

    if "generated_letter" in st.session_state:

        st.subheader("Generated Cover Letter")

        edited_letter = st.text_area(
            "Review and edit your letter",
            value=st.session_state.generated_letter,
            height=350
        )

        st.download_button(
            "Download Cover Letter",
            data=edited_letter,
            file_name="AI_JobPilot_Cover_Letter.txt",
            mime="text/plain"
        )


# --------------------------------------------------
# APPLICATION TRACKER
# --------------------------------------------------

elif page == "Application Tracker":

    st.title("📋 Application Tracker")

    st.write(
        "Track the jobs you have saved and update their application status."
    )

    applications = get_applications()

    if not applications:

        st.info(
            "You have not saved any jobs yet. "
            "Visit AI Job Matching or Job Search to save jobs."
        )

    else:

        st.metric(
            "Total Saved Applications",
            len(applications)
        )

        status_options = [
            "Saved",
            "Applied",
            "Assessment",
            "Interview",
            "Rejected",
            "Offer"
        ]

        for application in applications:

            with st.container(border=True):

                st.subheader(application["title"])

                st.write(
                    f"**Company:** {application['company']}"
                )

                st.write(
                    f"**Location:** {application['location']}"
                )

                st.write(
                    f"**Saved On:** {application['created_at']}"
                )

                current_status = application["status"]

                if current_status not in status_options:
                    current_status = "Saved"

                new_status = st.selectbox(
                    "Application Status",
                    status_options,
                    index=status_options.index(current_status),
                    key=f"status_{application['application_id']}"
                )

                new_notes = st.text_area(
                    "Notes",
                    value=application["notes"] or "",
                    key=f"notes_{application['application_id']}"
                )

                if st.button(
                    "Update Application",
                    key=f"update_{application['application_id']}"
                ):

                    update_application(
                        application["application_id"],
                        new_status,
                        new_notes
                    )

                    st.success("Application updated successfully.")

                if application.get("apply_url"):
                    st.link_button(
                        "Open Job Application",
                        application["apply_url"]
                    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.sidebar.divider()

st.sidebar.caption(
    "AI JobPilot | Minor Project"
)

st.sidebar.caption(
    "Resume Analysis • Semantic Matching • Job Tracking"
)
