
import numpy as np
import streamlit as st


@st.cache_resource
def load_model():
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2",
        device="cpu"
    )

    return model


def calculate_similarity(resume_text, job_description):
    model = load_model()

    embeddings = model.encode(
        [resume_text, job_description],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    score = np.dot(embeddings[0], embeddings[1])

    # Keep displayed score within 0-100.
    score = max(0.0, min(1.0, float(score)))

    return round(score * 100, 2)


def rank_jobs(resume_text, jobs):
    if not resume_text or not jobs:
        return []

    model = load_model()

    descriptions = [
        job.get("description", "") or job.get("title", "")
        for job in jobs
    ]

    resume_embedding = model.encode(
        resume_text,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    job_embeddings = model.encode(
        descriptions,
        convert_to_numpy=True,
        normalize_embeddings=True,
        batch_size=2,
        show_progress_bar=False
    )

    scores = np.dot(job_embeddings, resume_embedding)

    results = []

    for job, score in zip(jobs, scores):
        result = dict(job)

        score = max(0.0, min(1.0, float(score)))
        result["match_score"] = round(score * 100, 2)

        results.append(result)

    return sorted(
        results,
        key=lambda item: item["match_score"],
        reverse=True
    )
