from google.cloud import bigquery


def get_existing_certificate_ids(project_id: str) -> set[str]:
    """Retrieve known EPC certificate numbers from Bronze."""

    client = bigquery.Client(project=project_id)

    query = f"""
        SELECT certificate_number
        FROM `{project_id}.bronze.v_epc_certificate_ids`
    """

    results = client.query(query).result()

    return {
        row.certificate_number
        for row in results
    }


if __name__ == "__main__":
    existing_ids = get_existing_certificate_ids(
        project_id="dwellstack"
    )

    print("Existing certificates:", len(existing_ids))
    print("Sample:", list(existing_ids)[:5])
