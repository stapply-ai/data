import json
import sys
from pathlib import Path

from pydantic import ValidationError

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from export_utils import generate_job_id, write_jobs_csv  # noqa: E402
from models.lever import LeverJob  # noqa: E402


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

            job_list = data if isinstance(data, list) else data.get("postings", [])
            if not isinstance(job_list, list):
                continue

            for job_data in job_list:
                try:
                    job = LeverJob(**job_data)
                except ValidationError:
                    continue

                url = job.hostedUrl or job.applyUrl or ""
                ats_id = job.id or ""
                title = job.text or ""

                location_str = ""
                if job.categories:
                    if job.categories.location:
                        location_str = job.categories.location
                    elif job.categories.allLocations:
                        location_str = ", ".join(
                            loc for loc in job.categories.allLocations if loc
                        )
                if not location_str:
                    location_str = job.country or ""

                job_rows.append(
                    {
                        "url": url,
                        "title": title,
                        "location": location_str,
                        "company": company_name,
                        "ats_id": ats_id,
                        "id": generate_job_id("lever", url, ats_id),
                    }
                )

    print(f"Processed {len(job_rows)} total jobs")
    diff_path = write_jobs_csv(jobs_csv_path, job_rows)
    if diff_path:
        print(f"Created diff file: {diff_path.name}")


if __name__ == "__main__":
    main()
