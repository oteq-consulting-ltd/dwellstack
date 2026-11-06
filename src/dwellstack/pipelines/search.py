from dwellstack.api.client import search_certificates
from dwellstack.storage.bigquery import get_existing_certificate_ids


def find_new_certificates(
    project_id: str,
    council: str,
    date_start: str,
    date_end: str,
) -> set[str]:
    """Identify API certificates not already present in Bronze."""

    certificates = search_certificates(
        council=council,
        date_start=date_start,
        date_end=date_end,
        page_size=5000,
    )

    api_ids = {
        certificate["certificateNumber"]
        for certificate in certificates
    }

    existing_ids = get_existing_certificate_ids(project_id)

    return api_ids - existing_ids


if __name__ == "__main__":
    new_ids = find_new_certificates(
        project_id="dwellstack",
        council="Wolverhampton",
        date_start="2026-10-31",
        date_end="2026-10-31",
    )

    print("New certificates:", len(new_ids))
    print("Sample:", sorted(new_ids)[:5])
