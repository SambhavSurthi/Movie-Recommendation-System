from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class DataIngestionConfig:
    root_dir: Path
    source_URL: str
    local_data_file: Path
    dataset_name: str

@dataclass(frozen=True)
class DataTransformationConfig:
    root_dir: Path
    data_path: Path
    transformed_data_path: Path

@dataclass(frozen=True)
class ModelTrainerConfig:
    root_dir: Path
    transformed_data_path: Path
    model_name: str
    vectorizer_name: str
    indices_name: str

@dataclass(frozen=True)
class ModelEvaluationConfig:
    root_dir: Path
    model_path: Path
    evaluation_metric_name: str
