
import requests


def fetch_remotive_jobs(search=""):
    """Fetch remote jobs from the Remotive public API."""

    url = "https://remotive.com/api/remote-jobs"

    try:
        response = requests.get(
            url,
            params={"search": search} if search else {},
            timeout=20
        )
        response.raise_for_status()

        data = response.json()
        jobs = []

        for item in data.get("jobs", []):
            jobs.append({
                "external_id": "remotive-" + str(item.get("id")),
                "title": item.get("title", "Untitled"),
                "company": item.get("company_name", "Unknown"),
                "location": item.get("candidate_required_location", "Remote"),
                "country": item.get("candidate_required_location", "Not specified"),
                "job_type": item.get("job_type", "Not specified"),
                "work_mode": "Remote",
                "experience": "Not specified",
                "description": item.get("description", ""),
                "apply_url": item.get("url", ""),
                "source": "Remotive"
            })

        return jobs

    except requests.RequestException as error:
        print("Remotive API error:", error)
        return []


def fetch_arbeitnow_jobs():
    """Fetch jobs from the Arbeitnow job board API."""

    url = "https://www.arbeitnow.com/api/job-board-api"

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        data = response.json()
        jobs = []

        for item in data.get("data", []):
            location = item.get("location", "Not specified")
            is_remote = item.get("remote", False)

            jobs.append({
                "external_id": "arbeitnow-" + str(item.get("slug")),
                "title": item.get("title", "Untitled"),
                "company": item.get("company_name", "Unknown"),
                "location": location,
                "country": location,
                "job_type": "Not specified",
                "work_mode": "Remote" if is_remote else "On-site/Not specified",
                "experience": "Not specified",
                "description": item.get("description", ""),
                "apply_url": item.get("url", ""),
                "source": "Arbeitnow"
            })

        return jobs

    except requests.RequestException as error:
        print("Arbeitnow API error:", error)
        return []


def fetch_jobs(search=""):
    """Combine jobs from the available providers."""

    jobs = []

    jobs.extend(fetch_remotive_jobs(search))
    jobs.extend(fetch_arbeitnow_jobs())

    # Remove duplicate records by external ID.
    unique_jobs = {}

    for job in jobs:
        unique_jobs[job["external_id"]] = job

    return list(unique_jobs.values())
