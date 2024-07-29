
# Blood Pressure Tracker

This is a Blood Pressure Tracker application developed using Django. The application allows users to log their blood pressure readings, view trends and comparisons, and get insights based on country and global averages.

## Features

- **Log Blood Pressure Readings**: Users can log their systolic, diastolic, and pulse readings along with their country and sex.
- **View Averages and Trends**: Users can view their average readings and trends over time.
- **Comparisons**: Users can compare their readings against country and global averages.
- **Email Notifications**: Users receive email notifications if their readings are outside normal ranges.
- **Machine Learning**: Incorporates a RandomForest model to predict high blood pressure based on user data.

## Installation

### Prerequisites

- Python 3.10 or later
- Django 5.0.7
- Pandas
- Matplotlib
- Scikit-learn

## Create a Virtual Environment
1. python -m venv bp_env
2. source bp_env/bin/activate  # On Windows, use `bp_env\Scripts\activate`

## Instal Dependencies
pip install -r requirements.txt

## Configuring Environment Variables
Create a '.env' file in the project root and add the following environment variables:
- SECRET_KEY=your_secret_key
- DEBUG=True
- EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
- EMAIL_HOST=smtp.gmail.com
- EMAIL_PORT=587
- EMAIL_USE_TLS=True
- EMAIL_HOST_USER=your_email@gmail.com
- EMAIL_HOST_PASSWORD=your_email_password
- DEFAULT_FROM_EMAIL=your_email@gmail.com

## Run Migrations
- python manage.py makemigrations
- python manage.py migrate

## Create a Superuser
python manage.py createsuperuser

## Run the Development Server
python manage.py runserver

## Usage
- Navigate to http://127.0.0.1:8000/ in your web browser.
- Log in using the superuser account you created.
- Use the navigation bar to log readings, view averages and trends, and compare your readings.

## Testing
Run the tests to ensure everything is working correctly:
python manage.py test tracker

## Machine Learning Model
This application uses a RandomForestClassifier to predict high blood pressure based on user readings. The model is trained using the 'train_model.py' script.
To update the model:
1. Add new readings to the dataset
2. Run the script to retrain the model
python train_model.py

## License
This project is licensed under the MIT license



### Clone the Repository

```bash
git clone https://github.com/yourusername/yourrepository.git
cd yourrepository
 

