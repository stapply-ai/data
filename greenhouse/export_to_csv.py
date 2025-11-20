import json
import sys
from pathlib import Path

from pydantic import ValidationError

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from export_utils import generate_job_id, write_jobs_csv  # noqa: E402
from models.gh import GreenhouseJob  # noqa: E402


def main():
    companies_dir = Path(__file__).resolve().parent / "companies"
    jobs_csv_path = Path(__file__).resolve().parent / "jobs.csv"

    job_rows = []

    if not companies_dir.exists() or not companies_dir.is_dir():
        print(f"Companies directory does not exist: {companies_dir}")
    else:
        for json_file in sorted(companies_dir.glob("*.json")):
            company_name = json_file.stem
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                continue

            jobs = data.get("jobs", [])
            if not isinstance(jobs, list):
                continue

            for job_data in jobs:
                try:
                    job = GreenhouseJob(**job_data)
                except ValidationError:
                    continue

                location_obj = job.location
                location_str = (
                    location_obj.name if location_obj and location_obj.name else ""
                )
                url = job.absolute_url or ""
                ats_id = str(job.id) if job.id is not None else ""

                job_rows.append(
                    {
                        "url": url,
                        "title": job.title or "",
                        "location": location_str,
                        "company": company_name,
                        "ats_id": ats_id,
                        "id": generate_job_id("greenhouse", url, ats_id),
                    }
                )

    print(f"Processed {len(job_rows)} total jobs")
    diff_path = write_jobs_csv(jobs_csv_path, job_rows)
    if diff_path:
        print(f"Created diff file: {diff_path.name}")


if __name__ == "__main__":
    main()
