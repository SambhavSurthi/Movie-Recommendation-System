import sys
from src.exception import CustomException
from src.logger import logger
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from src.entity.config_entity import ModelTrainerConfig
from src.entity.artifact_entity import (
    DataTransformationArtifact,
    ModelTrainerArtifact
)
from src.utils.common import save_object, load_object
import pandas as pd
import scipy.sparse


class ModelTrainer:
    def __init__(self, config: ModelTrainerConfig, data_transformation_artifact: DataTransformationArtifact):
        self.config = config
        self.data_transformation_artifact = data_transformation_artifact

    def initiate_model_trainer(self) -> ModelTrainerArtifact:
        try:
            logger.info("Initiating Model Training (TF-IDF Vectorization)")

            transformed_data_path = self.data_transformation_artifact.transformed_data_path
            logger.info(f"Loading transformed data from {transformed_data_path}")
            
            df = load_object(file_path=transformed_data_path)

            logger.info("Creating TF-IDF Vectorizer")
            # Limit the features to avoid huge sparse matrices
            tfidf = TfidfVectorizer(stop_words='english', max_features=10000)

            logger.info("Fitting and transforming text data to tfidf matrix.. this might take a minute.")
            tfidf_matrix = tfidf.fit_transform(df['combined_features'])

            logger.info("Extracting indices wrapper map...")
            
            df = df.reset_index(drop=True)
            indices = pd.Series(df.index, index=df['title']).drop_duplicates()
            indices_dict = indices.to_dict()

            # Create paths
            model_path_obj = os.path.join(self.config.root_dir, self.config.model_name)
            vectorizer_path_obj = os.path.join(self.config.root_dir, self.config.vectorizer_name)
            indices_path_obj = os.path.join(self.config.root_dir, self.config.indices_name)

            logger.info("Saving trained artifacts to Models directory...")
            
            # save matrix
            save_object(file_path=model_path_obj, obj=tfidf_matrix)
            
            # save vectorizer
            save_object(file_path=vectorizer_path_obj, obj=tfidf)
            
            # save indices
            save_object(file_path=indices_path_obj, obj=indices_dict)

            logger.info("Model Training phase completed successfully!")

            return ModelTrainerArtifact(
                model_path=model_path_obj,
                vectorizer_path=vectorizer_path_obj,
                indices_path=indices_path_obj
            )

        except Exception as e:
            raise CustomException(e, sys)
