from src.pipeline.training_pipeline import TrainingPipeline
from src.logger import logger

def main():
    logger.info("Starting Main Execution Entrypoint...")
    training_pipeline = TrainingPipeline()
    training_pipeline.run_pipeline()
    logger.info("Main Execution Finished")

if __name__ == "__main__":
    main()
