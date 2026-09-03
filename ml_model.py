import os
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

from preprocess import load_and_preprocess_data

MODELS_DIR = os.path.join(os.path.dirname(__file__), 'models')
MODEL_PATH = os.path.join(MODELS_DIR, 'relevance_model.pkl')
VECTORIZER_PATH = os.path.join(MODELS_DIR, 'tfidf_vectorizer.pkl')

def train_and_evaluate_ml():
    """
    Trains TF-IDF Vectorizer + Logistic Regression model for Session Relevance Classification.
    
    Why Logistic Regression?
    1. High Explainability: Easy to explain feature weights/coefficients to non-technical stakeholders.
    2. Confidence Output: Provides calibrated probability scores (predict_proba) for confidence calculation.
    3. Lightweight & Fast: Ideal for small/synthetic datasets without heavy hyperparameter overhead.
    """
    os.makedirs(MODELS_DIR, exist_ok=True)
    df, _ = load_and_preprocess_data()

    X_text = df['normalized_text'].values
    y = df['relevance_label'].values

    # Train / Test split (80% train, 20% test)
    X_train_text, X_test_text, y_train, y_test = train_test_split(
        X_text, y, test_size=0.2, random_state=42, stratify=y
    )

    # 1. TF-IDF Feature Extraction
    vectorizer = TfidfVectorizer(max_features=500, ngram_range=(1, 2), stop_words='english')
    X_train_vec = vectorizer.fit_transform(X_train_text)
    X_test_vec = vectorizer.transform(X_test_text)

    # 2. Train Logistic Regression Model
    model = LogisticRegression(C=1.0, solver='lbfgs', max_iter=200, random_state=42)
    model.fit(X_train_vec, y_train)

    # 3. Model Evaluation on Test Split
    y_pred = model.predict(X_test_vec)
    y_prob = model.predict_proba(X_test_vec)[:, 1]

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    cm = confusion_matrix(y_test, y_pred).tolist()

    # 4. Save Trained Model and Vectorizer
    joblib.dump(model, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)

    metrics = {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "confusion_matrix": cm,
        "test_samples": len(y_test)
    }

    print(f"[SUCCESS] Saved ML Relevance Model to '{MODEL_PATH}'")
    print(f"[SUCCESS] Saved TF-IDF Vectorizer to '{VECTORIZER_PATH}'")
    return metrics

def predict_relevance(text_content):
    """
    Predicts relevance for a given session text snippet.
    Returns:
        dict: {
            "prediction": 1 (Relevant) or 0 (Not Relevant),
            "label": "Relevant" or "Not Relevant",
            "confidence": percentage (float e.g. 92.5),
            "low_confidence_flag": True if confidence < 70.0
        }
    """
    if not os.path.exists(MODEL_PATH) or not os.path.exists(VECTORIZER_PATH):
        train_and_evaluate_ml()

    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)

    normalized_input = str(text_content).lower().strip()
    vec = vectorizer.transform([normalized_input])
    
    pred = int(model.predict(vec)[0])
    probs = model.predict_proba(vec)[0]
    conf_score = float(probs[pred]) * 100.0

    return {
        "prediction": pred,
        "label": "Relevant" if pred == 1 else "Not Relevant",
        "confidence": round(conf_score, 1),
        "low_confidence_flag": bool(conf_score < 70.0)
    }

if __name__ == '__main__':
    print("=== ML RELEVANCE MODEL TRAINING ===")
    metrics = train_and_evaluate_ml()
    print("\nModel Evaluation Metrics:")
    for k, v in metrics.items():
        print(f"  - {k}: {v}")

    # Quick test sample
    sample_text = "Client discussed severe anxiety and requested study routine follow-up."
    res = predict_relevance(sample_text)
    print(f"\nSample Prediction Test:")
    print(f"  Input: '{sample_text}'")
    print(f"  Output: {res['label']} ({res['confidence']}% confidence)")
