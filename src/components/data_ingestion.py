import os
import sys
from src.exception import CustomException
from src.logger import logger
import pandas as pd
from src.entity.config_entity import DataIngestionConfig
from src.entity.artifact_entity import DataIngestionArtifact
from pathlib import Path
import shutil

class DataIngestion:
    def __init__(self, config: DataIngestionConfig):
        self.config = config

    def initiate_data_ingestion(self) -> DataIngestionArtifact:
        try:
            logger.info("Initiating Data Ingestion Component")
            
            # For this pipeline, assuming local copy from existing data
            # Real-world scenario might involve reading from S3 or SQL database
            local_data_path = self.config.local_data_file
            
            if not os.path.exists(local_data_path):
                raise Exception(f"Local data file not found at {local_data_path}")

            logger.info(f"Reading local dataset from {local_data_path}")
            
            # Make sure root dir exists
            os.makedirs(self.config.root_dir, exist_ok=True)
            
            destination_path = os.path.join(self.config.root_dir, os.path.basename(local_data_path))
            
            # Simple copy operation for ingestion simulating download/transfer
            shutil.copy2(local_data_path, destination_path)
            logger.info(f"Data copied to ingestion artifacts dir at {destination_path}")

            # Return the ingested artifact
            return DataIngestionArtifact(data_file_path=Path(destination_path))

        except Exception as e:
            raise CustomException(e, sys)
