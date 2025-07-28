"""
Machine Learning API Endpoints for Trust Engine
Comprehensive REST API for ML model training, prediction, and evaluation
Implements all thesis requirements for adaptive authentication ML pipeline
"""

from flask import Blueprint, request, jsonify, send_file
from flask_restful import Api, Resource
import pandas as pd
import numpy as np
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import traceback
import io
import base64

# Import Trust Engine ML modules - using lazy imports to avoid circular dependency
from app.utils import get_supabase_client, get_elasticsearch_client, load_sample_cicids2017_data
from app.auth import require_auth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
ml_bp = Blueprint('ml_api', __name__, url_prefix='/api/ml')
api = Api(ml_bp)

# Global ML engine instances - lazy initialization to avoid circular imports
ml_engine = None
evaluator = None
visualizer = None

def get_ml_engine():
    """Lazy initialization of ML engine"""
    global ml_engine
    if ml_engine is None:
        from app.ml_engine import TrustScoreMLEngine
        ml_engine = TrustScoreMLEngine()
    return ml_engine

def get_evaluator():
    """Lazy initialization of evaluator"""
    global evaluator
    if evaluator is None:
        from app.evaluation import TrustEngineEvaluator
        evaluator = TrustEngineEvaluator()
    return evaluator

def get_visualizer():
    """Lazy initialization of visualizer"""
    global visualizer
    if visualizer is None:
        from app.visualization import TrustEngineVisualizer
        visualizer = TrustEngineVisualizer()
    return visualizer

class MLHealthCheck(Resource):
    """Health check endpoint for ML services"""

    def get(self):
        """Check ML service status"""
        try:
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "ml_engine": "initialized",
                "classifiers_available": list(get_ml_engine().classifiers.keys()),
                "models_trained": len(get_ml_engine().trained_models) > 0,
                "version": "1.0.0"
            }, 200
        except Exception as e:
            logger.error(f"ML health check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e)}, 500

class TrainingResource(Resource):
    """ML Model Training Endpoints"""

    def post(self):
        """Train all ML classifiers with CICIDS2017 data"""
        try:
            data = request.get_json()

            # Configuration options
            config = {
                "use_sample_data": data.get("use_sample_data", True),
                "test_size": data.get("test_size", 0.2),
                "cross_validation": data.get("cross_validation", True),
                "cv_folds": data.get("cv_folds", 5),
                "save_models": data.get("save_models", True),
                "model_path": data.get("model_path", "models/")
            }

            logger.info(f"Starting ML training with config: {config}")

            # Load training data
            if config["use_sample_data"]:
                df = load_sample_cicids2017_data()
                logger.info(f"Loaded sample CICIDS2017 data: {df.shape}")
            else:
                # Load from Supabase or custom dataset
                supabase = get_supabase_client()
                response = supabase.table('telemetry_data').select('*').execute()
                df = pd.DataFrame(response.data)
                logger.info(f"Loaded telemetry data from Supabase: {df.shape}")

            if df.empty:
                return {"error": "No training data available"}, 400

            # Train all classifiers
            training_results = get_ml_engine().train_all_classifiers(
                df,
                test_size=config["test_size"],
                cross_validate=config["cross_validation"],
                cv_folds=config["cv_folds"]
            )

            # Save models if requested
            if config["save_models"]:
                model_paths = get_ml_engine().save_models(config["model_path"])
                training_results["model_paths"] = model_paths

            # Log training completion
            logger.info("ML training completed successfully")

            return {
                "status": "success",
                "message": "All classifiers trained successfully",
                "timestamp": datetime.utcnow().isoformat(),
                "training_results": training_results,
                "config": config
            }, 200

        except Exception as e:
            logger.error(f"Training failed: {str(e)}")
            logger.error(traceback.format_exc())
            return {"error": f"Training failed: {str(e)}"}, 500

class PredictionResource(Resource):
    """ML Prediction Endpoints"""

    def post(self):
        """Generate trust score predictions using trained models"""
        try:
            data = request.get_json()

            # Validate input
            if not data or 'features' not in data:
                return {"error": "Missing features in request"}, 400

            features = data['features']
            classifier_name = data.get('classifier', 'RandomForest')

            # Validate classifier
            if classifier_name not in get_ml_engine().trained_models:
                available = list(get_ml_engine().trained_models.keys())
                return {
                    "error": f"Classifier '{classifier_name}' not trained",
                    "available_classifiers": available
                }, 400

            # Make prediction
            prediction_result = get_ml_engine().predict_trust_score(features, classifier_name)

            # Add metadata
            prediction_result.update({
                "timestamp": datetime.utcnow().isoformat(),
                "classifier_used": classifier_name,
                "request_id": data.get("request_id", "unknown")
            })

            logger.info(f"Prediction made using {classifier_name}: {prediction_result['trust_score']}")

            return {
                "status": "success",
                "prediction": prediction_result
            }, 200

        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            return {"error": f"Prediction failed: {str(e)}"}, 500

class BatchPredictionResource(Resource):
    """Batch prediction endpoints for multiple samples"""

    def post(self):
        """Generate predictions for multiple feature sets"""
        try:
            data = request.get_json()

            if not data or 'batch_features' not in data:
                return {"error": "Missing batch_features in request"}, 400

            batch_features = data['batch_features']
            classifier_name = data.get('classifier', 'RandomForest')

            if not isinstance(batch_features, list):
                return {"error": "batch_features must be a list"}, 400

            # Validate classifier
            if classifier_name not in get_ml_engine().trained_models:
                available = list(get_ml_engine().trained_models.keys())
                return {
                    "error": f"Classifier '{classifier_name}' not trained",
                    "available_classifiers": available
                }, 400

            # Process batch predictions
            predictions = []
            for i, features in enumerate(batch_features):
                try:
                    prediction = get_ml_engine().predict_trust_score(features, classifier_name)
                    prediction['sample_id'] = i
                    predictions.append(prediction)
                except Exception as e:
                    logger.warning(f"Failed to predict sample {i}: {str(e)}")
                    predictions.append({
                        "sample_id": i,
                        "error": str(e),
                        "trust_score": None
                    })

            return {
                "status": "success",
                "timestamp": datetime.utcnow().isoformat(),
                "classifier_used": classifier_name,
                "total_samples": len(batch_features),
                "successful_predictions": len([p for p in predictions if 'error' not in p]),
                "predictions": predictions
            }, 200

        except Exception as e:
            logger.error(f"Batch prediction failed: {str(e)}")
            return {"error": f"Batch prediction failed: {str(e)}"}, 500

class EvaluationResource(Resource):
    """ML Model Evaluation Endpoints"""

    def get(self):
        """Get comprehensive model performance metrics"""
        try:
            # Get performance metrics for all trained models
            if not get_ml_engine().trained_models:
                return {"error": "No trained models available for evaluation"}, 400

            performance_metrics = {}

            for classifier_name in get_ml_engine().trained_models.keys():
                metrics = get_ml_engine().get_model_performance(classifier_name)
                if metrics:
                    performance_metrics[classifier_name] = metrics

            # Generate summary statistics
            summary = self._generate_performance_summary(performance_metrics)

            return {
                "status": "success",
                "timestamp": datetime.utcnow().isoformat(),
                "performance_metrics": get_ml_engine().performance_metrics,
                "summary": summary
            }, 200

        except Exception as e:
            logger.error(f"Evaluation failed: {str(e)}")
            return {"error": f"Evaluation failed: {str(e)}"}, 500

    def post(self):
        """Run comprehensive evaluation with test data"""
        try:
            data = request.get_json() or {}

            # Load test data
            test_data_source = data.get("test_data_source", "sample")

            if test_data_source == "sample":
                df = load_sample_cicids2017_data()
            else:
                # Custom test data handling
                return {"error": "Custom test data not implemented yet"}, 501

            if df.empty:
                return {"error": "No test data available"}, 400

            # Run evaluation
            evaluation_results = get_evaluator().comprehensive_evaluation(
                get_ml_engine().trained_models,
                df,
                output_dir=data.get("output_dir", "evaluation_results/")
            )

            return {
                "status": "success",
                "timestamp": datetime.utcnow().isoformat(),
                "evaluation_results": evaluation_results
            }, 200

        except Exception as e:
            logger.error(f"Comprehensive evaluation failed: {str(e)}")
            return {"error": f"Comprehensive evaluation failed: {str(e)}"}, 500

    def _generate_performance_summary(self, performance_metrics: Dict) -> Dict:
        """Generate summary statistics from performance metrics"""
        try:
            summary = {
                "best_accuracy": {"classifier": None, "score": 0},
                "best_f1": {"classifier": None, "score": 0},
                "best_auc": {"classifier": None, "score": 0},
                "average_metrics": {}
            }

            all_accuracy = []
            all_f1 = []
            all_auc = []

            for classifier, metrics in performance_metrics.items():
                accuracy = metrics.get('test_accuracy', 0)
                f1 = metrics.get('test_f1_score', 0)
                auc_score = metrics.get('test_auc', 0)

                all_accuracy.append(accuracy)
                all_f1.append(f1)
                all_auc.append(auc_score)

                # Track best performers
                if accuracy > summary["best_accuracy"]["score"]:
                    summary["best_accuracy"] = {"classifier": classifier, "score": accuracy}

                if f1 > summary["best_f1"]["score"]:
                    summary["best_f1"] = {"classifier": classifier, "score": f1}

                if auc_score > summary["best_auc"]["score"]:
                    summary["best_auc"] = {"classifier": classifier, "score": auc_score}

            # Calculate averages
            if all_accuracy:
                summary["average_metrics"] = {
                    "accuracy": np.mean(all_accuracy),
                    "f1_score": np.mean(all_f1),
                    "auc": np.mean(all_auc),
                    "std_accuracy": np.std(all_accuracy),
                    "std_f1": np.std(all_f1),
                    "std_auc": np.std(all_auc)
                }

            return summary

        except Exception as e:
            logger.error(f"Failed to generate performance summary: {str(e)}")
            return {"error": "Failed to generate summary"}

class VisualizationResource(Resource):
    """ML Visualization Endpoints"""

    def get(self, chart_type):
        """Generate ML evaluation charts"""
        try:
            # Supported chart types
            supported_charts = [
                'confusion_matrix', 'roc_curves', 'feature_importance',
                'performance_comparison', 'trust_score_distribution'
            ]

            if chart_type not in supported_charts:
                return {
                    "error": f"Unsupported chart type: {chart_type}",
                    "supported_charts": supported_charts
                }, 400

            # Check if models are trained
            if not get_ml_engine().trained_models:
                return {"error": "No trained models available for visualization"}, 400

            # Generate visualization based on type
            if chart_type == 'confusion_matrix':
                charts = get_visualizer().plot_confusion_matrices(get_ml_engine().trained_models)
            elif chart_type == 'roc_curves':
                charts = get_visualizer().plot_roc_curves(get_ml_engine().trained_models)
            elif chart_type == 'feature_importance':
                charts = get_visualizer().plot_feature_importance(get_ml_engine().trained_models)
            elif chart_type == 'performance_comparison':
                performance_data = {}
                for name in get_ml_engine().trained_models.keys():
                    performance_data[name] = get_ml_engine().get_model_performance(name)
                charts = visualizer.plot_classifier_comparison(performance_data)
            elif chart_type == 'trust_score_distribution':
                charts = get_visualizer().plot_trust_score_distribution(get_ml_engine().trained_models)

            return {
                "status": "success",
                "chart_type": chart_type,
                "timestamp": datetime.utcnow().isoformat(),
                "charts": charts
            }, 200

        except Exception as e:
            logger.error(f"Visualization generation failed: {str(e)}")
            return {"error": f"Visualization failed: {str(e)}"}, 500

class ModelManagementResource(Resource):
    """Model Management Endpoints"""

    def get(self):
        """Get information about trained models"""
        try:
            model_info = {
                "trained_models": list(get_ml_engine().trained_models.keys()),
                "available_classifiers": list(get_ml_engine().classifiers.keys()),
                "training_history": get_ml_engine().training_history[-10:],  # Last 10 entries
                "model_metadata": {}
            }

            # Add metadata for each trained model
            for model_name in get_ml_engine().trained_models.keys():
                performance = get_ml_engine().get_model_performance(model_name)
                model_info["model_metadata"][model_name] = {
                    "performance": performance,
                    "trained": True,
                    "classifier_type": type(get_ml_engine().classifiers[model_name]).__name__
                }

            return {
                "status": "success",
                "timestamp": datetime.utcnow().isoformat(),
                "model_info": model_info
            }, 200

        except Exception as e:
            logger.error(f"Model info retrieval failed: {str(e)}")
            return {"error": f"Model info failed: {str(e)}"}, 500

    def post(self):
        """Load saved models from disk"""
        try:
            data = request.get_json() or {}
            model_path = data.get("model_path", "models/")

            if not os.path.exists(model_path):
                return {"error": f"Model path does not exist: {model_path}"}, 400

            # Load models
            loaded_models = get_ml_engine().load_models(model_path)

            return {
                "status": "success",
                "message": f"Loaded {len(loaded_models)} models",
                "loaded_models": loaded_models,
                "timestamp": datetime.utcnow().isoformat()
            }, 200

        except Exception as e:
            logger.error(f"Model loading failed: {str(e)}")
            return {"error": f"Model loading failed: {str(e)}"}, 500

    def delete(self):
        """Clear all trained models from memory"""
        try:
            cleared_models = list(get_ml_engine().trained_models.keys())
            get_ml_engine().trained_models.clear()
            get_ml_engine().scalers.clear()
            get_ml_engine().performance_metrics.clear()

            return {
                "status": "success",
                "message": f"Cleared {len(cleared_models)} models from memory",
                "cleared_models": cleared_models,
                "timestamp": datetime.utcnow().isoformat()
            }, 200

        except Exception as e:
            logger.error(f"Model clearing failed: {str(e)}")
            return {"error": f"Model clearing failed: {str(e)}"}, 500

class BenchmarkResource(Resource):
    """Performance Benchmarking Endpoints"""

    def post(self):
        """Run performance benchmarks on trained models"""
        try:
            data = request.get_json() or {}

            # Benchmark configuration
            config = {
                "num_samples": data.get("num_samples", 1000),
                "iterations": data.get("iterations", 10),
                "measure_memory": data.get("measure_memory", True),
                "measure_latency": data.get("measure_latency", True)
            }

            if not get_ml_engine().trained_models:
                return {"error": "No trained models available for benchmarking"}, 400

            # Run benchmarks
            benchmark_results = get_ml_engine().benchmark_performance(
                num_samples=config["num_samples"],
                iterations=config["iterations"]
            )

            # Add system performance metrics
            system_metrics = self._get_system_metrics()

            return {
                "status": "success",
                "timestamp": datetime.utcnow().isoformat(),
                "benchmark_config": config,
                "benchmark_results": benchmark_results,
                "system_metrics": system_metrics
            }, 200

        except Exception as e:
            logger.error(f"Benchmarking failed: {str(e)}")
            return {"error": f"Benchmarking failed: {str(e)}"}, 500

    def _get_system_metrics(self) -> Dict:
        """Get current system performance metrics"""
        try:
            import psutil

            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "timestamp": datetime.utcnow().isoformat()
            }
        except ImportError:
            return {"error": "psutil not available for system metrics"}
        except Exception as e:
            return {"error": f"Failed to get system metrics: {str(e)}"}

# Register API resources
api.add_resource(MLHealthCheck, '/health')
api.add_resource(TrainingResource, '/train')
api.add_resource(PredictionResource, '/predict')
api.add_resource(BatchPredictionResource, '/predict/batch')
api.add_resource(EvaluationResource, '/evaluate')
api.add_resource(VisualizationResource, '/visualize/<string:chart_type>')
api.add_resource(ModelManagementResource, '/models')
api.add_resource(BenchmarkResource, '/benchmark')

# Traditional Flask routes for compatibility
@ml_bp.route('/status', methods=['GET'])
def ml_status():
    """Simple status endpoint"""
    return jsonify({
        "service": "Trust Engine ML API",
        "status": "active",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": [
            "/api/ml/health",
            "/api/ml/train",
            "/api/ml/predict",
            "/api/ml/predict/batch",
            "/api/ml/evaluate",
            "/api/ml/visualize/<chart_type>",
            "/api/ml/models",
            "/api/ml/benchmark"
        ]
    })

@ml_bp.route('/swagger', methods=['GET'])
def swagger_ui():
    """Swagger UI documentation endpoint"""
    return jsonify({
        "message": "Swagger UI documentation",
        "note": "Install flask-swagger-ui for interactive documentation",
        "api_endpoints": {
            "health": "GET /api/ml/health - Check ML service health",
            "train": "POST /api/ml/train - Train all ML classifiers",
            "predict": "POST /api/ml/predict - Single prediction",
            "batch_predict": "POST /api/ml/predict/batch - Batch predictions",
            "evaluate": "GET/POST /api/ml/evaluate - Model evaluation",
            "visualize": "GET /api/ml/visualize/<chart_type> - Generate charts",
            "models": "GET/POST/DELETE /api/ml/models - Model management",
            "benchmark": "POST /api/ml/benchmark - Performance benchmarking"
        }
    })

# Error handlers
@ml_bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "ML endpoint not found", "status": 404}), 404

@ml_bp.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal ML service error", "status": 500}), 500

@ml_bp.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request to ML service", "status": 400}), 400

if __name__ == '__main__':
    # For testing purposes
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(ml_bp)
    app.run(debug=True, port=5001)
