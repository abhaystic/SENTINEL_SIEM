# core/ai_engine.py
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import sqlite3
import os
import time
from collections import defaultdict


class SentinelAI:
    def __init__(self, db_path="db/sentinel.db"):
        self.db_path = db_path
        self.model = IsolationForest(
            n_estimators=150,
            contamination=0.08,
            random_state=42,
            max_samples='auto'
        )
        self.scaler = StandardScaler()
        self.is_trained = False

        # Rate-based tracker — counts requests per IP in a rolling window
        self.ip_request_counts = defaultdict(list)
        self.RATE_WINDOW = 60    # seconds
        self.RATE_THRESHOLD = 25 # requests in that window before flagging

        print("[SENTINEL AI] ML anomaly engine loaded.")

    def _clean_old_requests(self, ip):
        now = time.time()
        self.ip_request_counts[ip] = [
            t for t in self.ip_request_counts[ip]
            if now - t < self.RATE_WINDOW
        ]

    def check_rate_limit(self, ip):
        self._clean_old_requests(ip)
        self.ip_request_counts[ip].append(time.time())
        count = len(self.ip_request_counts[ip])
        if count >= self.RATE_THRESHOLD:
            return True, count
        return False, count

    def fetch_training_data(self):
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(
                "SELECT risk_score, is_threat, payload_length FROM security_logs",
                conn
            )
            conn.close()
            return df
        except Exception as e:
            print(f"[SENTINEL AI] Training data fetch error: {e}")
            return None

    def train_model(self):
        df = self.fetch_training_data()

        if df is not None and len(df) > 15:
            features = df[['risk_score', 'is_threat', 'payload_length']].fillna(0)
            scaled = self.scaler.fit_transform(features)
            self.model.fit(scaled)
            self.is_trained = True
            print(f"[SENTINEL AI] Model trained on {len(df)} historical records.")
        else:
            # fallback — train on synthetic baseline so the model is usable
            synthetic = pd.DataFrame({
                'risk_score':     [0]*40 + [50]*10 + [90]*5,
                'is_threat':      [0]*40 + [1]*10  + [1]*5,
                'payload_length': [20]*40 + [80]*10 + [200]*5
            })
            scaled = self.scaler.fit_transform(synthetic)
            self.model.fit(scaled)
            self.is_trained = True
            print("[SENTINEL AI] Trained on synthetic baseline (insufficient historical data).")

    def analyze_behavior(self, risk_score, is_threat_flag, payload_length=50):
        if not self.is_trained:
            return "UNKNOWN"

        try:
            test = pd.DataFrame({
                'risk_score':     [risk_score],
                'is_threat':      [int(is_threat_flag)],
                'payload_length': [payload_length]
            })
            scaled = self.scaler.transform(test)
            prediction = self.model.predict(scaled)
            anomaly_score = self.model.decision_function(scaled)[0]

            if prediction[0] == -1 and anomaly_score < -0.1:
                return "ANOMALY_DETECTED"
            return "NORMAL"
        except Exception as e:
            print(f"[SENTINEL AI] Analyze error: {e}")
            return "UNKNOWN"

    def get_threat_confidence(self, risk_score, payload_length=50):
        # Returns a 0-100 confidence score for threat probability
        if not self.is_trained:
            return risk_score

        try:
            test = self.scaler.transform([[risk_score, 1, payload_length]])
            raw_score = self.model.decision_function(test)[0]
            # Map decision function output to 0-100 scale
            confidence = max(0, min(100, int((1 - raw_score) * 50 + risk_score * 0.5)))
            return confidence
        except:
            return risk_score
