import os
import sys
from src.exception import CustomException
from src.logger import logger
from src.utils.common import load_object
import numpy as np
import pandas as pd
from typing import List, Tuple

class PredictionPipeline:
    def __init__(self):
        # We will load from default artifacts locations
        self.base_dir = "artifacts/model_trainer"
        self.data_dir = "artifacts/data_transformation"
        self.df = None
        self.indices = None
        self.tfidf_matrix = None

    def load_artifacts(self):
        try:
            logger.info("Loading Prediction Artifacts (DF, Indices, Matrix)...")
            
            # Load mapped indices dict
            self.indices = load_object(os.path.join(self.base_dir, "indices.pkl"))
            
            # Load sparse matrix
            self.tfidf_matrix = load_object(os.path.join(self.base_dir, "tfidf_matrix.pkl"))
            
            # Load transformed dataframe to get titles out
            self.df = load_object(os.path.join(self.data_dir, "df.pkl"))
            # Make sure index behavior is safe
            self.df = self.df.reset_index(drop=True)
            
            logger.info("Artifacts loaded successfully into PredictionPipeline")
            
        except Exception as e:
            raise CustomException(e, sys)

    def _norm_title(self, t: str) -> str:
        return str(t).strip().lower()

    def get_local_idx_by_title(self, title: str) -> int:
        if self.indices is None:
            raise Exception("Prediction pipeline resources not loaded.")
        
        # Build normalized map dynamically
        normalized_map = {self._norm_title(k): int(v) for k, v in self.indices.items()}
        key = self._norm_title(title)
        
        if key in normalized_map:
            return normalized_map[key]
        raise Exception(f"Title not found in local dataset: '{title}'")

    def recommend_titles(self, query_title: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """
        Returns list of (title, score) 
        """
        try:
            if self.df is None or self.tfidf_matrix is None:
                self.load_artifacts()

            idx = self.get_local_idx_by_title(query_title)

            # query vector
            qv = self.tfidf_matrix[idx]
            # Use scipy sparse efficient dot product
            scores = (self.tfidf_matrix.dot(qv.T)).toarray().ravel()

            # sort descending
            order = np.argsort(-scores)

            out = []
            for i in order:
                if int(i) == int(idx):
                    continue
                try:
                    title_i = str(self.df.iloc[int(i)]["title"])
                except Exception:
                    continue
                out.append((title_i, float(scores[int(i)])))
                if len(out) >= top_n:
                    break
            return out

        except Exception as e:
            logger.exception(f"Prediction Pipeline Error: {e}")
            raise CustomException(e, sys)
