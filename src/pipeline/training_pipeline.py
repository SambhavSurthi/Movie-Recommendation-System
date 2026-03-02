from src.config.configuration import ConfigurationManager
from src.components.data_ingestion import DataIngestion
from src.components.data_transformation import DataTransformation
from src.components.model_trainer import ModelTrainer
from src.components.model_evaluation import ModelEvaluation
from src.logger import logger
import sys
from src.exception import CustomException

class TrainingPipeline:
    def __init__(self):
        pass

    def run_pipeline(self):
        try:
            logger.info("========== TRAINING PIPELINE STARTED ==========")
            
            config = ConfigurationManager()
            
            # Data Ingestion
            data_ingestion_config = config.get_data_ingestion_config()
            data_ingestion = DataIngestion(config=data_ingestion_config)
            data_ingestion_artifact = data_ingestion.initiate_data_ingestion()

            # Data Transformation
            data_transformation_config = config.get_data_transformation_config()
            data_transformation = DataTransformation(
                config=data_transformation_config,
                data_ingestion_artifact=data_ingestion_artifact
            )
            data_transformation_artifact = data_transformation.initiate_data_transformation()

            # Model Trainer
            model_trainer_config = config.get_model_trainer_config()
            model_trainer = ModelTrainer(
                config=model_trainer_config,
                data_transformation_artifact=data_transformation_artifact
            )
            model_trainer_artifact = model_trainer.initiate_model_trainer()

            # Model Evaluation
            model_evaluation_config = config.get_model_evaluation_config()
            model_evaluation = ModelEvaluation(
                config=model_evaluation_config,
                model_trainer_artifact=model_trainer_artifact
            )
            model_evaluation_artifact = model_evaluation.initiate_model_evaluation()

            if not model_evaluation_artifact.is_model_accepted:
                raise Exception("Model is not accepted according to evaluation metrics.")

            logger.info("========== TRAINING PIPELINE COMPLETED SUCCESSFULLY ==========")

        except Exception as e:
            logger.exception(e)
            raise CustomException(e, sys)

if __name__ == "__main__":
    obj = TrainingPipeline()
    obj.run_pipeline()
