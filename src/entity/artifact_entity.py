from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass(frozen=True)
class DataIngestionArtifact:
    data_file_path: Path

@dataclass(frozen=True)
class DataTransformationArtifact:
    transformed_data_path: Path

@dataclass(frozen=True)
class ModelTrainerArtifact:
    model_path: Path
    vectorizer_path: Path
    indices_path: Path

@dataclass(frozen=True)
class ModelEvaluationArtifact:
    is_model_accepted: bool
    evaluated_model_path: Optional[Path] = None
