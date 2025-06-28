# run_all.py

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import os
import subprocess
import traceback
from src.utils.logger import get_logger

logger = get_logger(__name__)

def run_notebook(path, timeout=600):
    """
    Executes a Jupyter notebook from the pipeline
    """
    try:
        logger.info(f"Running notebook: {path}")
        with open(path, encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)
            ep = ExecutePreprocessor(timeout=timeout, kernel_name='python3')
            ep.preprocess(nb, {'metadata': {'path': os.path.dirname(path)}})
        logger.info(f"✅ Successfully ran notebook: {path}")
    except Exception as e:
        logger.error(f"Failed to run notebook {path}")
        logger.error(traceback.format_exc())

def run_script(path):
    """
    Runs a Python script using subprocess fromn the pipeline
    """
    try:
        logger.info(f"Running script: {path}")
        result = subprocess.run(["python", path], check=True, capture_output=True, text=True)
        logger.info(f"Successfully ran script: {path}")
        logger.debug(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running script: {path}")
        logger.error(e.stderr)

if __name__ == "__main__":
    logger.info("Starting full pipeline execution...\n")

    # Step 1: Get award winners
    run_script("src/data/get_award_winners.py")

    # Step 2: Scrape + update data
    run_script("src/data/update_data.py")

    # Step 3: Run EDA + cleaning notebooks
    eda_notebooks = [
        "notebooks/eda/01_clean_players.ipynb",
        "notebooks/eda/02_clean_teams.ipynb",
        "notebooks/eda/03_eda_player_awards.ipynb",
        "notebooks/eda/04_eda_dpoy_awards.ipynb",
        "notebooks/eda/05_eda_ppg_leader.ipynb",
        "notebooks/eda/06_eda_team.ipynb"
    ]
    for nb in eda_notebooks:
        run_notebook(nb)

    # Step 4: Run modeling notebooks
    modeling_notebooks = [
        "notebooks/modeling/07_model_dpoy_predictions.ipynb",
        "notebooks/modeling/08_model_mvp_predictions.ipynb",
        "notebooks/modeling/09_model_scoring_leader_predictions.ipynb",
        "notebooks/modeling/10_model_team_predictions.ipynb"
    ]
    for nb in modeling_notebooks:
        run_notebook(nb)

    logger.info("All steps completed successfully.")
