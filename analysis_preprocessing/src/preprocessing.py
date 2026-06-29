import pandas as pd
from sklearn.preprocessing import MinMaxScaler

def handle_missing_data(df):
    df_clean = df.copy()
    
    numerical_cols = ['Age', 'Braden_Score', 'ADL_Score']
    for col in numerical_cols:
        if df_clean[col].isnull().sum() > 0:
            median_value = df_clean[col].median()
            df_clean[col] = df_clean[col].fillna(median_value)
            
    categorical_cols = ['Cognitive_Status', 'Gender', 'Fall_Risk']
    for col in categorical_cols:
        if df_clean[col].isnull().sum() > 0:
            mode_value = df_clean[col].mode()[0]
            df_clean[col] = df_clean[col].fillna(mode_value)
            
    return df_clean

def transform_features(df):
    scaler = MinMaxScaler()
    numerical_cols = ['Age', 'Braden_Score', 'ADL_Score']
    df[numerical_cols] = scaler.fit_transform(df[numerical_cols])
    
    df = pd.get_dummies(df, columns=['Cognitive_Status', 'Gender', 'Fall_Risk'], drop_first=False)
    
    return df