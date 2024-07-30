import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import LabelEncoder
import os 

class BloodPressureModel:
    def __init__(self, data_path, model_path):
        self.data_path = data_path
        self.model_path = model_path
        self.encoder_path = encoder_path
        self.model = None
        self.encoder = LabelEncoder()
        self.data = None
        self.X = None
        self.y = None

    def load_data(self):
        self.data = pd.read_csv(self.data_path)
    
    def preprocess_data(self):
        # Convert categorical variables to numerical ones
        self.data['sex'] = self.data['sex'].map({'Male': 0, 'Female': 1})
        self.data['country'] = self.encoder.fit_transform(self.data['country'])
        
        # Create target variables
        self.data['systolic_target'] = (self.data['systolic'] > 140).astype(int)
        self.data['diastolic_target'] = (self.data['diastolic'] > 80).astype(int)
        
        # Split the data into features and target
        self.X = self.data.drop(['systolic', 'diastolic', 'Unnamed: 0', 'Prevalence of raised blood pressure', 'Year'], axis=1) 
        self.y = self.data[['systolic_target', 'diastolic_target']]
        
        # Debug prints to check for NaNs
        print("Checking for NaNs in the dataset:")
        print(self.X.isnull().sum())
        
        # Verify there are no NaNs
        assert not self.X.isnull().values.any(), "Features contain NaN values" # Searching for NaN values
        assert not self.y.isnull().values.any(), "Target contains NaN values" # Searching for NaN values


    def train_model(self):
        # Split into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(self.X, self.y, test_size=0.2, random_state=42)
        
        # Train the model
        self.model = MultiOutputRegressor(RandomForestRegressor())
        self.model.fit(X_train, y_train)
        
        # Model accuracy
        train_score= self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)
        print(f"Model train accuracy: {train_score:.2f}")
        print(f"Model test accuracy: {test_score:.2f}")

    def save_model(self):
        # Save the model
        joblib.dump(self.model, self.model_path)
    
    def run(self):
        self.load_data()
        self.preprocess_data()
        self.train_model()
        self.save_model()

# Usage
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_path = os.path.join(BASE_DIR, 'data', 'bp_standardised_cleaned.csv')
model_path = os.path.join(BASE_DIR, 'models', 'bp_model.pkl')
encoder_path = os.path.join(BASE_DIR, 'models', 'label_encoder.pkl')
bp_model = BloodPressureModel(data_path, model_path)
bp_model.run()
