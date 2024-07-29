# Blood pressure data based on 
# country and sex

import pandas as pd
import os
import logging
from django.db.models import Avg 


logger = logging.getLogger(__name__)


# Get project base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Counstruct path for data
data_path = os.path.join(BASE_DIR, 'data', 'bp_standardised_cleaned.csv')

# Load in the dataset
data = pd.read_csv(data_path)

# Calculate the averages per sex and per country
country_sex_avg = data.groupby(['country', 'sex']).agg({'systolic': 'mean', 'diastolic': 'mean'}).reset_index()

# Calculate the global averages per sex
global_sex_avg = data.groupby('sex').agg({'systolic': 'mean', 'diastolic': 'mean'}).reset_index()


# Function to fetch blood pressure ranges
def get_blood_pressure_range(sex, country):
    logger.debug(f"Fetching blood pressure range for sex: {sex}, country: {country}")

    # Check if country is available in the dataset
    country_avg = country_sex_avg[(country_sex_avg['country'].str.lower() == country.lower()) & (country_sex_avg['sex'].str.lower() == sex.lower())]
    if not country_avg.empty:
        avg_systolic = country_avg['systolic'].mean()
        avg_diastolic = country_avg['diastolic'].mean()
        logger.debug(f"Found country averages: systolic={avg_systolic}, diastolic={avg_diastolic}")
        return {
            'country': {
                'systolic': [avg_systolic - 10, avg_systolic + 10],
                'diastolic': [avg_diastolic - 10, avg_diastolic + 10]
            },
            'default': {
                'systolic': [90, 120],
                'diastolic': [60, 80]
            }
        }
    else:
        logger.debug(f"No country averages found for country: {country}, sex: {sex}")

    # Check global averages
    global_avg = global_sex_avg[global_sex_avg['sex'].str.lower() == sex.lower()]
    if not global_avg.empty:
        avg_systolic = global_avg['systolic'].mean()
        avg_diastolic = global_avg['diastolic'].mean()
        logger.debug(f"Found global averages: systolic={avg_systolic}, diastolic={avg_diastolic}")
        return {
            'global': {
                'systolic': [avg_systolic - 10, avg_systolic + 10],
                'diastolic': [avg_diastolic - 10, avg_diastolic + 10]
            },
            'default': {
                'systolic': [90, 120],
                'diastolic': [60, 80]
            }
        }

    logger.debug("Returning default averages")
    return {
        'default': {
            'systolic': [90, 120],
            'diastolic': [60, 80]
        }
    }