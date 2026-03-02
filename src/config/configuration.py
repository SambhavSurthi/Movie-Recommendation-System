from src.utils.common import read_yaml, create_directories
from src.entity.config_entity import (
    DataIngestionConfig,
    DataTransformationConfig,
    ModelTrainerConfig,
    ModelEvaluationConfig
)
from pathlib import Path
import os
from src.exception import CustomException
import sys

# Constants for default config paths
CONFIG_FILE_PATH = Path("config/config.yaml")

class ConfigurationManager:
    def __init__(self, config_filepath=CONFIG_FILE_PATH):
        try:
            self.config = read_yaml(config_filepath)
            create_directories([self.config.artifacts_root])
        except Exception as e:
            raise CustomException(e, sys)

    def get_data_ingestion_config(self) -> DataIngestionConfig:
        try:
            config = self.config.data_ingestion
            create_directories([config.root_dir])

            data_ingestion_config = DataIngestionConfig(
                root_dir=Path(config.root_dir),
                source_URL=config.source_URL,
                local_data_file=Path(config.local_data_file),
                dataset_name=config.dataset_name
            )
            return data_ingestion_config
        except Exception as e:
            raise CustomException(e, sys)

    def get_data_transformation_config(self) -> DataTransformationConfig:
        try:
            config = self.config.data_transformation
            create_directories([config.root_dir])

            data_transformation_config = DataTransformationConfig(
                root_dir=Path(config.root_dir),
                data_path=Path(config.data_path),
                transformed_data_path=Path(config.transformed_data_path)
            )
            return data_transformation_config
        except Exception as e:
            raise CustomException(e, sys)

    def get_model_trainer_config(self) -> ModelTrainerConfig:
        try:
            config = self.config.model_trainer
            create_directories([config.root_dir])

            model_trainer_config = ModelTrainerConfig(
                root_dir=Path(config.root_dir),
                transformed_data_path=Path(config.transformed_data_path),
                model_name=config.model_name,
                vectorizer_name=config.vectorizer_name,
                indices_name=config.indices_name
            )
            return model_trainer_config
        except Exception as e:
            raise CustomException(e, sys)

    def get_model_evaluation_config(self) -> ModelEvaluationConfig:
        try:
            config = self.config.model_evaluation
            create_directories([config.root_dir])

            model_evaluation_config = ModelEvaluationConfig(
                root_dir=Path(config.root_dir),
                model_path=Path(config.model_path),
                evaluation_metric_name=config.evaluation_metric_name
            )
            return model_evaluation_config
        except Exception as e:
            raise CustomException(e, sys)
