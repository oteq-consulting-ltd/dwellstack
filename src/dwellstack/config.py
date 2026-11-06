from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gcp_project_id: str
    gcp_region: str = "europe-west2"
    gcp_raw_bucket: str
    bq_dataset_id: str = "dwellstack_analytics_dev"
    epc_api_key: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
