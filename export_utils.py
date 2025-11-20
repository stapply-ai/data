from __future__ import annotations

import csv
from datetime import datetime
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from urllib.parse import urlparse
from uuid import NAMESPACE_URL, uuid5


FIELDNAMES = ["url", "title", "location", "company", "ats_id", "id"]


def generate_job_id(platform: str, url: str | None, ats_id: str | None) -> str:
    """
    Generate a deterministic UUID for a job using the platform, ats_id, and URL.
    Falls back gracefully when values are missing so the ID stays stable
    between runs.
    """
    platform = platform or "unknown"
    url = url or ""
    ats_id = ats_id or ""
    unique_key = f"{platform}:{ats_id}:{url}"
    return str(uuid5(NAMESPACE_URL, unique_key))


def _extract_ats_id_from_url(url: str) -> str:
    """
    Extract ats_id from URL if it's embedded in the path.
    Supports multiple URL formats:
    - Ashby: https://jobs.ashbyhq.com/company/uuid-ats-id
    - Lever: https://jobs.lever.co/company/uuid-ats-id
    - Greenhouse: https://boards.greenhouse.io/company/jobs/numeric-id
    - Workable: https://apply.workable.com/j/alphanumeric-id
    Returns the ats_id or empty string if not found.
    """
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split("/") if p]

        if not path_parts:
            return ""

        # Greenhouse URLs: /company/jobs/numeric-id
        if "/jobs/" in parsed.path or "greenhouse.io" in parsed.netloc:
            # Find the segment after "/jobs/"
            try:
                jobs_index = path_parts.index("jobs")
                if jobs_index + 1 < len(path_parts):
                    return path_parts[jobs_index + 1]
            except ValueError:
                pass

        # Workable URLs: /j/alphanumeric-id
        if "/j/" in parsed.path or "workable.com" in parsed.netloc:
            try:
                j_index = path_parts.index("j")
                if j_index + 1 < len(path_parts):
                    return path_parts[j_index + 1]
            except ValueError:
                pass

        # Default: use last segment (works for Ashby and Lever UUIDs)
        # Accept any non-empty last segment as it could be an ID
        last_part = path_parts[-1]
        if last_part:
            return last_part

    except Exception:
        pass
    return ""


def _build_row_key(row: Dict[str, str]) -> str:
    """
    Build a comparable key for a job row using only ats_id.
    If ats_id is missing, try to extract it from the URL.
    Returns the ats_id or empty string if not available.
    """
    ats_id = (row.get("ats_id") or "").strip()
    if not ats_id:
        # Fallback: extract from URL if ats_id column doesn't exist
        url = (row.get("url") or "").strip()
        ats_id = _extract_ats_id_from_url(url)
    return ats_id


def _rows_equal(row_a: Dict[str, str], row_b: Dict[str, str]) -> bool:
    """
    Compare rows for equality, excluding the 'id' field since it's our local generated ID.
    Only compare the actual job data fields.
    """
    # Compare all fields except 'id' (which is our local generated UUID)
    fields_to_compare = [f for f in FIELDNAMES if f != "id"]
    for field in fields_to_compare:
        if (row_a.get(field) or "").strip() != (row_b.get(field) or "").strip():
            return False
    return True


def _compute_diff(
    previous_rows: Iterable[Dict[str, str]], new_rows: Iterable[Dict[str, str]]
) -> List[Dict[str, str]]:
    previous_index = {_build_row_key(row): row for row in previous_rows}
    new_index = {_build_row_key(row): row for row in new_rows}
    diff_rows: List[Dict[str, str]] = []

    # Find new or updated jobs
    for row in new_rows:
        key = _build_row_key(row)
        previous = previous_index.get(key)
        if previous is None:
            # New job
            diff_row = row.copy()
            diff_row["status"] = "new"
            diff_rows.append(diff_row)
        elif not _rows_equal(previous, row):
            # Updated job
            diff_row = row.copy()
            diff_row["status"] = "updated"
            diff_rows.append(diff_row)

    # Find removed jobs
    for row in previous_rows:
        key = _build_row_key(row)
        if key not in new_index:
            # Removed job
            diff_row = row.copy()
            diff_row["status"] = "removed"
            diff_rows.append(diff_row)

    return diff_rows


def write_jobs_csv(jobs_csv_path: Path, rows: List[Dict[str, str]]) -> Path | None:
    """
    Write the jobs CSV with all current jobs, and when a previous file exists,
    emit a diff file that contains only new, updated, or removed jobs with a status field.

    Returns the diff file path if one was created.
    """
    jobs_csv_path = Path(jobs_csv_path)
    jobs_csv_path.parent.mkdir(parents=True, exist_ok=True)

    diff_path: Path | None = None
    previous_rows: List[Dict[str, str]] = []

    if jobs_csv_path.exists():
        backup_path = jobs_csv_path.with_name(f"{jobs_csv_path.stem}_old{jobs_csv_path.suffix}")
        shutil.copy2(jobs_csv_path, backup_path)
        with open(jobs_csv_path, "r", encoding="utf-8", newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            previous_rows = list(reader)

        # Normalize previous_rows: ensure ats_id exists (extract from URL if missing)
        for row in previous_rows:
            if "ats_id" not in row or not row.get("ats_id", "").strip():
                url = row.get("url", "").strip()
                extracted_ats_id = _extract_ats_id_from_url(url)
                if extracted_ats_id:
                    row["ats_id"] = extracted_ats_id
            # Ensure all expected fields exist with empty defaults
            for field in FIELDNAMES:
                if field not in row:
                    row[field] = ""

        diff_rows = _compute_diff(previous_rows, rows)
        if diff_rows:  # Only create diff file if there are changes
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            diff_filename = (
                f"{jobs_csv_path.stem}_diff_{timestamp}{jobs_csv_path.suffix}"
            )
            diff_path = jobs_csv_path.with_name(diff_filename)

            # Diff file includes status field
            diff_fieldnames = FIELDNAMES + ["status"]
            with open(diff_path, "w", encoding="utf-8", newline="") as diff_file:
                writer = csv.DictWriter(diff_file, fieldnames=diff_fieldnames)
                writer.writeheader()
                writer.writerows(diff_rows)

    # Main jobs.csv contains all current jobs (no status field)
    with open(jobs_csv_path, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    return diff_path
