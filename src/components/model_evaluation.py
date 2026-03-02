import sys
from src.exception import CustomException
from src.logger import logger
from src.entity.config_entity import ModelEvaluationConfig
from src.entity.artifact_entity import (
    ModelTrainerArtifact,
    ModelEvaluationArtifact
)
from src.utils.common import load_object
import os


class ModelEvaluation:
    def __init__(self, config: ModelEvaluationConfig, model_trainer_artifact: ModelTrainerArtifact):
        self.config = config
        self.model_trainer_artifact = model_trainer_artifact

    def initiate_model_evaluation(self) -> ModelEvaluationArtifact:
        try:
            logger.info("Initiating Model Evaluation...")

            model_path = self.model_trainer_artifact.model_path
            logger.info(f"Loading evaluated model from {model_path}")
            
            tfidf_matrix = load_object(file_path=model_path)

            logger.info("Performing sanity metrics (shape checks, sparsity)")
            
            rows, cols = tfidf_matrix.shape
            logger.info(f"Shape of TF-IDF matrix: {rows} documents x {cols} features.")
            
            # Condition to accept model: more than 0 rows and columns
            is_model_accepted = True if (rows > 0 and cols > 0) else False

            logger.info(f"Model Evaluation completed. Model Accepted: {is_model_accepted}")

            return ModelEvaluationArtifact(
                is_model_accepted=is_model_accepted,
                evaluated_model_path=model_path if is_model_accepted else None
            )

        except Exception as e:
            raise CustomException(e, sys)
