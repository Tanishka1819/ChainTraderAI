import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import hashlib
import json
import pickle

class AITrader:
    def __init__(self, sequence_length=60):
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.sequence_length = sequence_length
        self.is_trained = False
        self.model_hash = None
        
    def prepare_data(self, data):
        """Prepare data for LSTM model"""
        # Ensure data is in the right format
        if isinstance(data, pd.DataFrame):
            prices = data['Close'].values.reshape(-1, 1)
        else:
            prices = np.array(data).reshape(-1, 1)
        
        # Scale the data
        scaled_data = self.scaler.fit_transform(prices)
        
        # Create sequences
        X, y = [], []
        for i in range(self.sequence_length, len(scaled_data)):
            X.append(scaled_data[i-self.sequence_length:i, 0])
            y.append(scaled_data[i, 0])
        
        return np.array(X), np.array(y)
    
    def build_model(self, input_shape):
        """Build LSTM model"""
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50, return_sequences=True),
            Dropout(0.2),
            LSTM(50),
            Dropout(0.2),
            Dense(25),
            Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mean_squared_error')
        return model
    
    def train(self, data, epochs=50, batch_size=32):
        """Train the AI model"""
        print("Preparing data...")
        X, y = self.prepare_data(data)
        
        if len(X) == 0:
            raise ValueError("Not enough data to train the model")
        
        print(f"Training with {len(X)} samples...")
        
        # Reshape X for LSTM
        X = X.reshape((X.shape[0], X.shape[1], 1))
        
        # Build model
        self.model = self.build_model((X.shape[1], 1))
        
        # Train model
        history = self.model.fit(X, y, epochs=epochs, batch_size=batch_size, verbose=1, validation_split=0.2)
        
        self.is_trained = True
        self.model_hash = self.generate_model_hash()
        
        print(f"Model trained successfully! Model hash: {self.model_hash}")
        return history
    
    def predict_next_price(self, recent_data):
        """Predict next price based on recent data"""
        if not self.is_trained or self.model is None:
            raise ValueError("Model must be trained before making predictions")
        
        # Prepare data
        if len(recent_data) < self.sequence_length:
            raise ValueError(f"Need at least {self.sequence_length} data points")
        
        # Take last sequence_length values
        last_sequence = recent_data[-self.sequence_length:].reshape(-1, 1)
        scaled_sequence = self.scaler.transform(last_sequence)
        
        # Reshape for prediction
        X_pred = scaled_sequence.reshape((1, self.sequence_length, 1))
        
        # Make prediction
        prediction_scaled = self.model.predict(X_pred, verbose=0)
        prediction = self.scaler.inverse_transform(prediction_scaled)
        
        return float(prediction[0][0])
    
    def generate_trading_signal(self, current_price, predicted_price, threshold=0.02):
        """Generate trading signal based on prediction"""
        price_change = (predicted_price - current_price) / current_price
        
        if price_change > threshold:
            return "BUY"
        elif price_change < -threshold:
            return "SELL"
        else:
            return "HOLD"
    
    def generate_model_hash(self):
        """Generate hash for model versioning"""
        if self.model is None:
            return None
        
        # Create a hash based on model weights
        weights_str = str(self.model.get_weights())
        model_info = {
            "sequence_length": self.sequence_length,
            "weights_hash": hashlib.sha256(weights_str.encode()).hexdigest()[:16]
        }
        
        return hashlib.sha256(json.dumps(model_info, sort_keys=True).encode()).hexdigest()[:16]