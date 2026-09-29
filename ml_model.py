import os
import functools
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

@functools.lru_cache(maxsize=1)
def load_ml_model_and_vectorizer():
    """
    Loads and caches the ML relevance model and TF-IDF vectorizer in memory.
    Prevents reloading and unpickling model from disk on every prediction call.
    """
    if not os.path.exists(MODEL_PATH) or not os.path.exists(VECTORIZER_PATH):
        train_and_evaluate_ml()

    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)
    return model, vectorizer

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

    # Clear cached model in case of retraining
    load_ml_model_and_vectorizer.cache_clear()

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
    Predicts relevance for a single text input using cached ML model & vectorizer.
    """
    res = predict_relevance_batch([text_content])
    return res[0] if res else {
        "prediction": 0,
        "label": "Not Relevant",
        "confidence": 50.0,
        "low_confidence_flag": True
    }

def predict_relevance_batch(text_list):
    """
    Predicts relevance for a list of session text snippets in a SINGLE batch pass.
    Transforms all texts with the cached TF-IDF vectorizer in one operation.
    
    Args:
        text_list (list of str): List of session text strings.
        
    Returns:
        list of dict: List of ML prediction result objects.
    """
    if not text_list:
        return []

    model, vectorizer = load_ml_model_and_vectorizer()

    normalized_inputs = [str(t).lower().strip() for t in text_list]
    vec = vectorizer.transform(normalized_inputs)
    
    preds = model.predict(vec)
    probs = model.predict_proba(vec)

    results = []
    for pred, prob_pair in zip(preds, probs):
        p_val = int(pred)
        conf_score = float(prob_pair[p_val]) * 100.0
        results.append({
            "prediction": p_val,
            "label": "Relevant" if p_val == 1 else "Not Relevant",
            "confidence": round(conf_score, 1),
            "low_confidence_flag": bool(conf_score < 70.0)
        })

    return results

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
