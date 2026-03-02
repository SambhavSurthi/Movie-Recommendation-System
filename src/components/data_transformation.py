import sys
from dataclasses import dataclass
import numpy as np 
import pandas as pd
from typing import Tuple
from src.exception import CustomException
from src.logger import logger
import os
from src.entity.config_entity import DataTransformationConfig
from src.entity.artifact_entity import (
    DataIngestionArtifact,
    DataTransformationArtifact
)
from src.utils.common import save_object

class DataTransformation:
    def __init__(self, config: DataTransformationConfig, data_ingestion_artifact: DataIngestionArtifact):
        self.config = config
        self.data_ingestion_artifact = data_ingestion_artifact

    def initiate_data_transformation(self) -> DataTransformationArtifact:
        try:
            logger.info("Initiating Data Transformation Component")
            
            # Loading data
            data_file_path = self.data_ingestion_artifact.data_file_path
            logger.info(f"Reading data from {data_file_path}")
            df = pd.read_csv(data_file_path, low_memory=False)
            
            logger.info(f"Initial shape of the dataframe is {df.shape}")

            # Feature Engineering
            logger.info("Applying feature combinations...")
            df = df.dropna(subset=['title'])
            
            # Helper logic from original script
            def fill_and_combine(row):
                genres = str(row['genres']) if pd.notna(row['genres']) else ""
                overview = str(row['overview']) if pd.notna(row['overview']) else ""
                tagline = str(row['tagline']) if pd.notna(row['tagline']) else ""
                return genres + " " + overview + " " + tagline

            # We use combined features to compute similarity
            df['combined_features'] = df.apply(fill_and_combine, axis=1)

            logger.info("Dropping unnecessary columns and saving required data...")
            # For demonstration, keeping title and combined_features
            if 'id' in df.columns:
                df['tmdb_id'] = df['id']
            
            transformed_df = df[['title', 'combined_features', 'tmdb_id']] if 'tmdb_id' in df.columns else df[['title', 'combined_features']]

            logger.info(f"Shape of the final dataframe before save is {transformed_df.shape}")

            # Save transformed dataframe physically
            save_object(
                file_path=self.config.transformed_data_path,
                obj=transformed_df
            )
            
            logger.info(f"Data Transformation completed and object saved to {self.config.transformed_data_path}")

            return DataTransformationArtifact(
                 transformed_data_path=self.config.transformed_data_path
            )

        except Exception as e:
            raise CustomException(e, sys)
