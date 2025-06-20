Folder Strucutre:

nba_awards_prediction/
├── config/
│   └── settings.yaml             # Configuration for file paths, retrain frequency, thresholds, etc.
│
├── data/
│   ├── raw/                      # Raw scraped data
│   ├── processed/                # Cleaned & preprocessed data
│   ├── external/                 # Any third-party datasets (e.g., team records, schedules)
│   └── interim/                  # Data mid-way through transformations
│
├── notebooks/
│   ├── eda/                      # EDA and data exploration
│   └── modeling/                 # ML and DL model development notebooks
│
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── scrape.py             # Web scraping logic
│   │   ├── preprocess.py         # Data cleaning and feature engineering
│   │   └── update_data.py        # Scheduled script to update data
│   │
│   ├── models/
│   │   ├── train_ml.py           # ML model training logic
│   │   ├── train_dl.py           # Deep learning model training logic
│   │   ├── evaluate.py           # Model evaluation and comparison
│   │   └── predict.py            # Generate predictions
│   │
│   ├── utils/
│   │   ├── logger.py             # Custom logger for tracking runs
│   │   └── helpers.py            # Common helper functions
│   │
│   └── dashboard/
│       ├── app.py                # Main dashboard logic (Streamlit or Dash)
│       └── visuals.py            # Functions to generate charts/plots
│
├── models/
│   ├── ml/                       # Saved ML model artifacts
│   └── dl/                       # Saved DL model artifacts
│
├── automation/
│   └── retrain_pipeline.py      # Entrypoint for retraining and re-predicting
│
├── tests/
│   ├── test_scrape.py
│   ├── test_preprocess.py
│   └── test_model.py
│
├── .gitignore
├── README.md
├── requirements.txt             # Python package dependencies
└── run_all.py                   # Script to run end-to-end pipeline manually
