"""
Machine Learning Engine for Trust Score Classification
Implements 4 core classifiers and 2 adaptive variants for thesis evaluation
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                           confusion_matrix, roc_curve, auc, classification_report)
from sklearn.pipeline import Pipeline
import joblib
import logging
from datetime import datetime
import os
from typing import Dict, List, Tuple, Any, Optional
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class TrustScoreMLEngine:
    """
    Machine Learning Engine for Trust Score Classification
    Implements thesis requirements for adaptive authentication
    """

    def __init__(self):
        self.classifiers = {}
        self.trained_models = {}
        self.scalers = {}
        self.label_encoders = {}
        self.feature_names = []
        self.training_history = []
        self.performance_metrics = {}

        # Initialize classifiers
        self._initialize_classifiers()

    def _initialize_classifiers(self):
        """Initialize all 6 classifiers (4 core + 2 adaptive variants)"""

        # 1. Random Forest - Robust to noise, high interpretability
        self.classifiers['RandomForest'] = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )

        # 2. K-Nearest Neighbors - Effective for outlier detection
        self.classifiers['KNN'] = KNeighborsClassifier(
            n_neighbors=5,
            weights='distance',
            algorithm='auto',
            metric='minkowski'
        )

        # 3. Naïve Bayes - Lightweight baseline with fast inference
        self.classifiers['NaiveBayes'] = GaussianNB(
            var_smoothing=1e-9
        )

        # 4. Multi-Layer Perceptron - Neural network for non-linear relationships
        self.classifiers['MLP'] = MLPClassifier(
            hidden_layer_sizes=(100, 50),
            activation='relu',
            solver='adam',
            alpha=0.0001,
            learning_rate='adaptive',
            max_iter=500,
            random_state=42
        )

        # 5. Adaptive K-Nearest Neighbors (AdKNN) - Hyperparameter tuning
        self.classifiers['AdaptiveKNN'] = GridSearchCV(
            KNeighborsClassifier(),
            param_grid={
                'n_neighbors': [3, 5, 7, 9, 11],
                'weights': ['uniform', 'distance'],
                'metric': ['euclidean', 'manhattan', 'minkowski']
            },
            cv=5,
            scoring='f1_weighted',
            n_jobs=-1
        )

        # 6. Adaptive Random Forest (AdRF) - Optimizer enhancements
        self.classifiers['AdaptiveRandomForest'] = GridSearchCV(
            RandomForestClassifier(random_state=42),
            param_grid={
                'n_estimators': [50, 100, 200],
                'max_depth': [5, 10, 15, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            },
            cv=5,
            scoring='f1_weighted',
            n_jobs=-1
        )

        logger.info("Initialized 6 ML classifiers for Trust Engine")

    def prepare_features(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare features for ML training/prediction
        Maps CICIDS2017 and telemetry data to STRIDE categories
        """
        # Use all numeric columns except 'Label' as features
        feature_columns = [col for col in data.columns if col != 'Label' and data[col].dtype in ['int64', 'float64']]

        # Store feature names for consistent prediction
        if not hasattr(self, 'feature_names') or not self.feature_names:
            self.feature_names = feature_columns
            logger.info(f"Stored {len(self.feature_names)} feature names for consistent prediction")

        # Handle missing columns by creating default values
        for col in self.feature_names:
            if col not in data.columns:
                data[col] = 0.0

        # Extract features
        X = data[feature_columns].fillna(0)

        # Map labels to STRIDE categories for trust scoring
        if 'Label' in data.columns:
            y = data['Label']
            # Convert attack types to trust score categories
            y = y.map(self._map_to_stride_categories)
        else:
            # Default trust score (for prediction scenarios)
            y = np.ones(len(X)) * 5  # Medium trust

        self.feature_names = feature_columns
        return X.values, y.values

    def _map_to_stride_categories(self, label: str) -> int:
        """
        Map attack labels to STRIDE-based trust scores (1-10 scale)
        Lower scores = higher risk, higher scores = higher trust
        """
        stride_mapping = {
            # High Risk Attacks (Low Trust Score 1-3)
            'DDoS': 1,  # Denial of Service
            'DoS GoldenEye': 1,
            'DoS Hulk': 1,
            'DoS Slowhttptest': 1,
            'DoS slowloris': 1,
            'Heartbleed': 1,  # Information Disclosure

            # Medium-High Risk (Trust Score 2-4)
            'PortScan': 2,  # Information Disclosure
            'FTP-Patator': 3,  # Elevation of Privilege
            'SSH-Patator': 3,
            'Web Attack – Brute Force': 3,
            'Web Attack – XSS': 3,  # Tampering
            'Web Attack – Sql Injection': 2,  # Tampering

            # Medium Risk (Trust Score 4-6)
            'Infiltration': 4,  # Spoofing/Tampering
            'Bot': 5,  # Repudiation

            # Low Risk/Normal (Trust Score 7-10)
            'BENIGN': 10,  # High trust
            'Normal': 10,

            # Default for unknown
            'Unknown': 5
        }

        return stride_mapping.get(str(label).strip(), 5)

    def train_all_classifiers(self, data: pd.DataFrame,
                            test_size: float = 0.2,
                            cross_validate: bool = True,
                            cv_folds: int = 5) -> Dict[str, Dict]:
        """
        Train all 6 classifiers and return performance metrics

        Args:
            data: Training dataset
            test_size: Proportion of data to use for testing
            cross_validate: Whether to perform cross-validation
            cv_folds: Number of folds for cross-validation
        """
        logger.info("Starting training of all ML classifiers...")

        # Prepare data
        X, y = self.prepare_features(data)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        # Scale features for neural networks and KNN
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        self.scalers['standard'] = scaler

        results = {}

        # Train each classifier
        for name, classifier in self.classifiers.items():
            logger.info(f"Training {name}...")

            start_time = datetime.now()

            try:
                # Use scaled data for neural networks and KNN variants
                if name in ['MLP', 'KNN', 'AdaptiveKNN']:
                    classifier.fit(X_train_scaled, y_train)
                    y_pred = classifier.predict(X_test_scaled)
                    y_pred_proba = self._get_prediction_probabilities(
                        classifier, X_test_scaled, name
                    )
                else:
                    classifier.fit(X_train, y_train)
                    y_pred = classifier.predict(X_test)
                    y_pred_proba = self._get_prediction_probabilities(
                        classifier, X_test, name
                    )

                # Calculate metrics
                training_time = (datetime.now() - start_time).total_seconds()

                metrics = self._calculate_metrics(y_test, y_pred, y_pred_proba)
                metrics['training_time'] = training_time
                metrics['model_name'] = name

                # Store trained model
                self.trained_models[name] = classifier
                results[name] = metrics

                # Cross-validation score (if enabled)
                if cross_validate:
                    if name in ['MLP', 'KNN', 'AdaptiveKNN']:
                        cv_scores = cross_val_score(classifier, X_train_scaled, y_train, cv=cv_folds)
                    else:
                        cv_scores = cross_val_score(classifier, X_train, y_train, cv=cv_folds)

                    results[name]['cv_mean'] = cv_scores.mean()
                    results[name]['cv_std'] = cv_scores.std()
                else:
                    results[name]['cv_mean'] = None
                    results[name]['cv_std'] = None

                logger.info(f"✅ {name} training completed - Accuracy: {metrics['accuracy']:.4f}")

            except Exception as e:
                logger.error(f"❌ Error training {name}: {str(e)}")
                results[name] = {'error': str(e), 'training_time': 0}

        # Store training results
        self.performance_metrics = results
        self.training_history.append({
            'timestamp': datetime.now(),
            'data_size': len(data),
            'results': results
        })

        logger.info("🎉 All classifiers training completed!")
        return results

    def _get_prediction_probabilities(self, classifier, X_test, name: str):
        """Get prediction probabilities if available"""
        try:
            if hasattr(classifier, 'predict_proba'):
                return classifier.predict_proba(X_test)
            elif hasattr(classifier, 'decision_function'):
                # For SVM-like classifiers
                return classifier.decision_function(X_test)
            else:
                return None
        except:
            return None

    def _calculate_metrics(self, y_true, y_pred, y_pred_proba=None) -> Dict:
        """Calculate comprehensive performance metrics"""

        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, average='weighted', zero_division=0),
            'recall': recall_score(y_true, y_pred, average='weighted', zero_division=0),
            'f1_score': f1_score(y_true, y_pred, average='weighted', zero_division=0),
            'confusion_matrix': confusion_matrix(y_true, y_pred).tolist(),
            'classification_report': classification_report(y_true, y_pred, zero_division=0)
        }

        # False Negative Rate calculation
        cm = confusion_matrix(y_true, y_pred)
        if cm.shape[0] > 1:
            # For multi-class, calculate average FNR
            fnr_per_class = []
            for i in range(cm.shape[0]):
                fn = cm[i, :].sum() - cm[i, i]  # False negatives for class i
                tp_fn = cm[i, :].sum()  # True positives + False negatives
                fnr = fn / tp_fn if tp_fn > 0 else 0
                fnr_per_class.append(fnr)
            metrics['false_negative_rate'] = np.mean(fnr_per_class)
        else:
            metrics['false_negative_rate'] = 0

        # ROC Curve and AUC (for binary/multi-class)
        if y_pred_proba is not None:
            try:
                # Handle multi-class ROC
                from sklearn.preprocessing import label_binarize
                from sklearn.metrics import roc_curve, auc
                from itertools import cycle

                n_classes = len(np.unique(y_true))
                if n_classes == 2:
                    # Binary classification
                    if y_pred_proba.ndim > 1:
                        fpr, tpr, _ = roc_curve(y_true, y_pred_proba[:, 1])
                    else:
                        fpr, tpr, _ = roc_curve(y_true, y_pred_proba)
                    roc_auc = auc(fpr, tpr)
                    metrics['roc_auc'] = roc_auc
                    metrics['roc_curve'] = {'fpr': fpr.tolist(), 'tpr': tpr.tolist()}
                else:
                    # Multi-class ROC (one-vs-rest)
                    y_bin = label_binarize(y_true, classes=np.unique(y_true))
                    if y_pred_proba.shape[1] == n_classes:
                        roc_auc = {}
                        for i in range(n_classes):
                            fpr, tpr, _ = roc_curve(y_bin[:, i], y_pred_proba[:, i])
                            roc_auc[f'class_{i}'] = auc(fpr, tpr)
                        metrics['roc_auc'] = np.mean(list(roc_auc.values()))
                        metrics['roc_auc_per_class'] = roc_auc
            except Exception as e:
                logger.warning(f"Could not calculate ROC curve: {e}")
                metrics['roc_auc'] = 0

        return metrics

    def predict_trust_score(self, features: Dict, model_name: str = 'RandomForest') -> Dict:
        """
        Predict trust score for a single session/VM
        Returns real-time authentication decision
        """
        if model_name not in self.trained_models:
            raise ValueError(f"Model {model_name} not trained yet")

        # Convert features to array using stored feature names order
        if not hasattr(self, 'feature_names') or not self.feature_names:
            raise ValueError("No feature names stored. Train models first.")

        # Create feature array in correct order
        feature_values = []
        for feature_name in self.feature_names:
            if feature_name in features:
                feature_values.append(features[feature_name])
            else:
                feature_values.append(0.0)  # Default value for missing features

        feature_array = np.array([feature_values]).reshape(1, -1)

        # Scale if needed
        if model_name in ['MLP', 'KNN', 'AdaptiveKNN'] and 'standard' in self.scalers:
            feature_array = self.scalers['standard'].transform(feature_array)

        # Predict
        start_time = datetime.now()

        classifier = self.trained_models[model_name]
        trust_score = classifier.predict(feature_array)[0]

        # Get prediction confidence if possible
        confidence = 0.5
        if hasattr(classifier, 'predict_proba'):
            proba = classifier.predict_proba(feature_array)[0]
            confidence = np.max(proba)

        latency = (datetime.now() - start_time).total_seconds() * 1000  # ms

        # Determine MFA requirement based on trust score
        mfa_required = trust_score < 5  # Low trust requires MFA
        access_decision = "ALLOW" if trust_score >= 3 else "DENY"

        return {
            'trust_score': float(trust_score),
            'confidence': float(confidence),
            'mfa_required': mfa_required,
            'access_decision': access_decision,
            'authentication_latency_ms': latency,
            'model_used': model_name,
            'timestamp': datetime.now().isoformat(),
            'stride_risk_level': self._get_stride_risk_level(trust_score)
        }

    def _get_stride_risk_level(self, trust_score: float) -> str:
        """Map trust score to STRIDE risk level"""
        if trust_score >= 8:
            return "LOW_RISK"
        elif trust_score >= 5:
            return "MEDIUM_RISK"
        elif trust_score >= 3:
            return "HIGH_RISK"
        else:
            return "CRITICAL_RISK"

    def get_model_performance(self, model_name: str = None) -> Dict:
        """Get comprehensive performance metrics for a specific model or all models"""
        if model_name is not None:
            # Return performance for specific model
            if model_name in self.performance_metrics:
                return self.performance_metrics[model_name]
            else:
                return {}
        else:
            # Return performance for all models
            return {
                'trained_models': list(self.trained_models.keys()),
                'performance_metrics': self.performance_metrics,
                'training_history': self.training_history,
                'feature_count': len(self.feature_names),
                'feature_names': self.feature_names
            }

    def save_models(self, directory: str = "models"):
        """Save all trained models to disk"""
        os.makedirs(directory, exist_ok=True)

        saved_models = []
        for name, model in self.trained_models.items():
            filename = os.path.join(directory, f"{name}_model.joblib")
            joblib.dump(model, filename)
            saved_models.append(filename)

        # Save scalers
        for name, scaler in self.scalers.items():
            filename = os.path.join(directory, f"{name}_scaler.joblib")
            joblib.dump(scaler, filename)
            saved_models.append(filename)

        logger.info(f"💾 Saved {len(saved_models)} model files to {directory}")
        return saved_models

    def load_models(self, directory: str = "models"):
        """Load trained models from disk"""
        loaded_models = []

        for filename in os.listdir(directory):
            if filename.endswith('_model.joblib'):
                name = filename.replace('_model.joblib', '')
                model_path = os.path.join(directory, filename)
                self.trained_models[name] = joblib.load(model_path)
                loaded_models.append(name)
            elif filename.endswith('_scaler.joblib'):
                name = filename.replace('_scaler.joblib', '')
                scaler_path = os.path.join(directory, filename)
                self.scalers[name] = joblib.load(scaler_path)

        logger.info(f"📂 Loaded {len(loaded_models)} models from {directory}")
        return loaded_models

    def benchmark_performance(self, num_samples: int = 1000,
                            iterations: int = 5) -> Dict:
        """
        Benchmark system performance metrics for thesis evaluation
        """
        from app.utils import load_sample_cicids2017_data

        logger.info(f"🏁 Starting performance benchmark with {num_samples} sessions...")

        # Load sample data for benchmarking
        data = load_sample_cicids2017_data()
        X, _ = self.prepare_features(data.head(num_samples))

        benchmark_results = {}

        for name, model in self.trained_models.items():
            # Prepare data for model
            if name in ['MLP', 'KNN', 'AdaptiveKNN'] and 'standard' in self.scalers:
                X_test = self.scalers['standard'].transform(X)
            else:
                X_test = X

            # Measure throughput (predictions per second)
            start_time = datetime.now()
            predictions = model.predict(X_test)
            end_time = datetime.now()

            total_time = (end_time - start_time).total_seconds()
            throughput = len(predictions) / total_time if total_time > 0 else 0
            avg_latency = (total_time / len(predictions)) * 1000  # ms per prediction

            benchmark_results[name] = {
                'throughput_sessions_per_second': throughput,
                'average_authentication_latency_ms': avg_latency,
                'total_processing_time_seconds': total_time,
                'sessions_processed': len(predictions),
                'predictions_sample': predictions[:10].tolist()
            }

        logger.info("🏆 Performance benchmark completed!")
        return benchmark_results

# Global ML Engine instance
ml_engine = TrustScoreMLEngine()
