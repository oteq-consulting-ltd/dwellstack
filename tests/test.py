import pandas as pd

df = pd.read_csv(
    "sample_data/wolverhampton_certs.csv",
    dtype={"uprn": "string"},
    low_memory=False
)

cert_counts = df["uprn"].value_counts()

print("Unique Properties:", df["uprn"].nunique())
print("Missing UPRN:", df["uprn"].isna().sum())
print("UPRNs with multiple certs:", (cert_counts > 1).sum())
print("Max certs for single UPRN:", cert_counts.max())
