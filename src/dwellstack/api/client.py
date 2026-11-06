import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.get-energy-performance-data.communities.gov.uk"


def search_certificates(
    council: str,
    date_start: str,
    date_end: str,
    page_size: int,
) -> list[dict]:
    """Retrieve all EPC search results for a council and date range."""

    token = os.environ["API_BEARER_TOKEN"]
    certificates = []
    page = 1

    while page is not None:
        response = requests.get(
            f"{BASE_URL}/api/domestic/search",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "council[]": council,
                "date_start": date_start,
                "date_end": date_end,
                "current_page": page,
                "page_size": page_size,
            },
            timeout=30,
        )

        if not response.ok:
            print("API error:", response.status_code, response.text)

        response.raise_for_status()
        result = response.json()

        ids = [row["certificateNumber"] for row in result["data"]]

        print(
            f"Page {page}: "
            f"{len(ids)} records, "
            f"first={ids[0] if ids else None}, "
            f"last={ids[-1] if ids else None}"
        )

        certificates.extend(result["data"])
        page = result["pagination"]["nextPage"]

    return certificates


def get_certificate(certificate_number: str) -> dict:
    """Retrieve the full JSON details for one EPC certificate."""

    token = os.environ["API_BEARER_TOKEN"]

    response = requests.get(
        f"{BASE_URL}/api/certificate",
        headers={"Authorization": f"Bearer {token}"},
        params={"certificate_number": certificate_number},
        timeout=30,
    )

    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    response = get_certificate(
        "2106-5193-2221-5174-4712"
    )

    certificate = response["data"]

    print("Payload type:", type(certificate).__name__)
    print("Fields returned:", len(certificate))
    print("Sample fields:", list(certificate)[:10])
