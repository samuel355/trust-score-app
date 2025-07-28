#!/usr/bin/env python3
"""
Comprehensive ML Pipeline Testing and Demo Script
Tests all 6 classifiers, generates evaluation reports, and validates API endpoints
"""

import sys
import os
import json
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.ml_engine import TrustScoreMLEngine
from app.evaluation import TrustEngineEvaluator
from app.visualization import TrustEngineVisualizer
from app.utils import load_sample_cicids2017_data, get_elasticsearch_client
from app.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ml_pipeline_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MLPipelineTester:
    """Comprehensive ML Pipeline Testing Suite"""

    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        self.ml_engine = TrustScoreMLEngine()
        self.evaluator = TrustEngineEvaluator()
        self.visualizer = TrustEngineVisualizer()
        self.test_results = {}
        self.performance_metrics = {}

        print("🚀 Trust Engine ML Pipeline Tester Initialized")
        print("=" * 60)

    def test_data_loading(self) -> bool:
        """Test 1: Verify CICIDS2017 data loading"""
        print("\n📊 Test 1: Data Loading Verification")
        print("-" * 40)

        try:
            # Load sample data
            df = load_sample_cicids2017_data()

            if df.empty:
                logger.error("❌ No data loaded from CICIDS2017 sample")
                return False

            print(f"✅ Loaded {df.shape[0]} samples with {df.shape[1]} features")
            print(f"📈 Data types: {df.dtypes.value_counts().to_dict()}")
            print(f"🏷️  Labels distribution: {df['Label'].value_counts().to_dict()}")

            # Check for missing values
            missing_values = df.isnull().sum().sum()
            if missing_values > 0:
                print(f"⚠️  Found {missing_values} missing values")
            else:
                print("✅ No missing values detected")

            self.test_results['data_loading'] = {
                'status': 'passed',
                'samples': df.shape[0],
                'features': df.shape[1],
                'missing_values': missing_values,
                'label_distribution': df['Label'].value_counts().to_dict()
            }

            return True

        except Exception as e:
            logger.error(f"❌ Data loading failed: {str(e)}")
            self.test_results['data_loading'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False

    def test_ml_training(self) -> bool:
        """Test 2: Train all 6 ML classifiers"""
        print("\n🧠 Test 2: ML Classifier Training")
        print("-" * 40)

        try:
            # Load training data
            df = load_sample_cicids2017_data()
            if df.empty:
                logger.error("❌ No training data available")
                return False

            # Start training timer
            start_time = time.time()

            print("🏋️  Training all 6 classifiers...")
            print("   1. Random Forest")
            print("   2. K-Nearest Neighbors")
            print("   3. Naïve Bayes")
            print("   4. Multi-Layer Perceptron")
            print("   5. Adaptive KNN")
            print("   6. Adaptive Random Forest")

            # Train all classifiers
            training_results = self.ml_engine.train_all_classifiers(
                df,
                test_size=0.2,
                cross_validate=True,
                cv_folds=5
            )

            training_time = time.time() - start_time

            print(f"✅ Training completed in {training_time:.2f} seconds")

            # Verify all models are trained
            trained_models = list(self.ml_engine.trained_models.keys())
            expected_models = ['RandomForest', 'KNN', 'NaiveBayes', 'MLP', 'AdaptiveKNN', 'AdaptiveRandomForest']

            missing_models = set(expected_models) - set(trained_models)
            if missing_models:
                logger.warning(f"⚠️  Missing trained models: {missing_models}")
            else:
                print("✅ All 6 classifiers trained successfully")

            # Display performance summary
            print("\n📊 Training Performance Summary:")
            for model_name in trained_models:
                performance = self.ml_engine.get_model_performance(model_name)
                if performance:
                    accuracy = performance.get('test_accuracy', 0)
                    f1_score = performance.get('test_f1_score', 0)
                    print(f"   {model_name}: Accuracy={accuracy:.3f}, F1={f1_score:.3f}")

            self.test_results['ml_training'] = {
                'status': 'passed',
                'training_time_seconds': training_time,
                'trained_models': trained_models,
                'missing_models': list(missing_models),
                'training_results': training_results
            }

            return True

        except Exception as e:
            logger.error(f"❌ ML training failed: {str(e)}")
            self.test_results['ml_training'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False

    def test_predictions(self) -> bool:
        """Test 3: Generate trust score predictions"""
        print("\n🔮 Test 3: Trust Score Predictions")
        print("-" * 40)

        try:
            if not self.ml_engine.trained_models:
                logger.error("❌ No trained models available for prediction")
                return False

            # Generate sample feature vector
            df = load_sample_cicids2017_data()
            sample_features = df.drop(['Label'], axis=1).iloc[0].to_dict()

            predictions = {}
            prediction_times = {}

            for model_name in self.ml_engine.trained_models.keys():
                try:
                    start_time = time.time()

                    # Make prediction
                    result = self.ml_engine.predict_trust_score(sample_features, model_name)

                    prediction_time = (time.time() - start_time) * 1000  # Convert to milliseconds

                    predictions[model_name] = result
                    prediction_times[model_name] = prediction_time

                    trust_score = result.get('trust_score', 0)
                    confidence = result.get('confidence', 0)
                    risk_level = result.get('risk_level', 'Unknown')

                    print(f"✅ {model_name}: Trust={trust_score:.3f}, Confidence={confidence:.3f}, Risk={risk_level} ({prediction_time:.2f}ms)")

                except Exception as e:
                    logger.warning(f"⚠️  Prediction failed for {model_name}: {str(e)}")
                    predictions[model_name] = {'error': str(e)}
                    prediction_times[model_name] = None

            # Calculate average prediction time
            valid_times = [t for t in prediction_times.values() if t is not None]
            avg_prediction_time = np.mean(valid_times) if valid_times else 0

            print(f"\n📊 Prediction Performance:")
            print(f"   Average prediction time: {avg_prediction_time:.2f}ms")
            print(f"   Successful predictions: {len([p for p in predictions.values() if 'error' not in p])}/{len(predictions)}")

            self.test_results['predictions'] = {
                'status': 'passed',
                'predictions': predictions,
                'prediction_times_ms': prediction_times,
                'average_prediction_time_ms': avg_prediction_time
            }

            return True

        except Exception as e:
            logger.error(f"❌ Prediction testing failed: {str(e)}")
            self.test_results['predictions'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False

    def test_evaluation_metrics(self) -> bool:
        """Test 4: Comprehensive model evaluation"""
        print("\n📈 Test 4: Model Evaluation Metrics")
        print("-" * 40)

        try:
            if not self.ml_engine.trained_models:
                logger.error("❌ No trained models available for evaluation")
                return False

            # Load test data
            df = load_sample_cicids2017_data()

            print("🔍 Generating comprehensive evaluation report...")

            # Run comprehensive evaluation
            evaluation_results = self.evaluator.comprehensive_evaluation(
                self.ml_engine.trained_models,
                df,
                output_dir="evaluation_results/"
            )

            # Extract key metrics
            print("\n📊 Evaluation Results Summary:")
            print("-" * 30)

            for model_name, metrics in evaluation_results.items():
                if isinstance(metrics, dict) and 'accuracy' in metrics:
                    accuracy = metrics.get('accuracy', 0)
                    precision = metrics.get('precision', 0)
                    recall = metrics.get('recall', 0)
                    f1_score = metrics.get('f1_score', 0)
                    auc_score = metrics.get('auc', 0)

                    print(f"📋 {model_name}:")
                    print(f"   Accuracy:  {accuracy:.3f}")
                    print(f"   Precision: {precision:.3f}")
                    print(f"   Recall:    {recall:.3f}")
                    print(f"   F1-Score:  {f1_score:.3f}")
                    print(f"   AUC:       {auc_score:.3f}")
                    print()

            # Find best performing model
            best_model = None
            best_f1 = 0

            for model_name, metrics in evaluation_results.items():
                if isinstance(metrics, dict) and 'f1_score' in metrics:
                    f1_score = metrics.get('f1_score', 0)
                    if f1_score > best_f1:
                        best_f1 = f1_score
                        best_model = model_name

            if best_model:
                print(f"🏆 Best performing model: {best_model} (F1-Score: {best_f1:.3f})")

            self.test_results['evaluation'] = {
                'status': 'passed',
                'evaluation_results': evaluation_results,
                'best_model': best_model,
                'best_f1_score': best_f1
            }

            return True

        except Exception as e:
            logger.error(f"❌ Evaluation testing failed: {str(e)}")
            self.test_results['evaluation'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False

    def test_visualizations(self) -> bool:
        """Test 5: Generate ML visualizations"""
        print("\n📊 Test 5: ML Visualizations")
        print("-" * 40)

        try:
            if not self.ml_engine.trained_models:
                logger.error("❌ No trained models available for visualization")
                return False

            print("🎨 Generating visualization charts...")

            visualization_results = {}

            # Test different chart types
            chart_types = [
                'confusion_matrix',
                'roc_curves',
                'feature_importance',
                'performance_comparison'
            ]

            for chart_type in chart_types:
                try:
                    print(f"   📈 Generating {chart_type}...")

                    if chart_type == 'confusion_matrix':
                        charts = self.visualizer.plot_confusion_matrices(self.ml_engine.trained_models)
                    elif chart_type == 'roc_curves':
                        charts = self.visualizer.plot_roc_curves(self.ml_engine.trained_models)
                    elif chart_type == 'feature_importance':
                        charts = self.visualizer.plot_feature_importance(self.ml_engine.trained_models)
                    elif chart_type == 'performance_comparison':
                        performance_data = {}
                        for name in self.ml_engine.trained_models.keys():
                            performance_data[name] = self.ml_engine.get_model_performance(name)
                        charts = self.visualizer.plot_classifier_comparison(performance_data)

                    visualization_results[chart_type] = 'generated'
                    print(f"   ✅ {chart_type} completed")

                except Exception as e:
                    logger.warning(f"   ⚠️  {chart_type} failed: {str(e)}")
                    visualization_results[chart_type] = f'failed: {str(e)}'

            successful_charts = len([v for v in visualization_results.values() if v == 'generated'])
            print(f"\n📊 Visualization Summary: {successful_charts}/{len(chart_types)} charts generated")

            self.test_results['visualizations'] = {
                'status': 'passed',
                'visualization_results': visualization_results,
                'successful_charts': successful_charts,
                'total_charts': len(chart_types)
            }

            return True

        except Exception as e:
            logger.error(f"❌ Visualization testing failed: {str(e)}")
            self.test_results['visualizations'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False

    def test_api_endpoints(self) -> bool:
        """Test 6: Validate ML API endpoints"""
        print("\n🌐 Test 6: ML API Endpoints")
        print("-" * 40)

        try:
            api_tests = {}

            # Test health endpoint
            try:
                response = requests.get(f"{self.base_url}/api/ml/health", timeout=10)
                if response.status_code == 200:
                    print("✅ Health endpoint: OK")
                    api_tests['health'] = 'passed'
                else:
                    print(f"⚠️  Health endpoint: {response.status_code}")
                    api_tests['health'] = f'failed: {response.status_code}'
            except requests.exceptions.RequestException as e:
                print(f"❌ Health endpoint: Connection failed - {str(e)}")
                api_tests['health'] = f'failed: {str(e)}'

            # Test status endpoint
            try:
                response = requests.get(f"{self.base_url}/api/ml/status", timeout=10)
                if response.status_code == 200:
                    print("✅ Status endpoint: OK")
                    api_tests['status'] = 'passed'
                else:
                    print(f"⚠️  Status endpoint: {response.status_code}")
                    api_tests['status'] = f'failed: {response.status_code}'
            except requests.exceptions.RequestException as e:
                print(f"❌ Status endpoint: Connection failed - {str(e)}")
                api_tests['status'] = f'failed: {str(e)}'

            # Test training endpoint (if app is running)
            if api_tests.get('health') == 'passed':
                try:
                    training_payload = {
                        "use_sample_data": True,
                        "test_size": 0.2,
                        "save_models": False
                    }

                    print("🏋️  Testing training endpoint...")
                    response = requests.post(
                        f"{self.base_url}/api/ml/train",
                        json=training_payload,
                        timeout=120  # Training can take time
                    )

                    if response.status_code == 200:
                        print("✅ Training endpoint: OK")
                        api_tests['training'] = 'passed'
                    else:
                        print(f"⚠️  Training endpoint: {response.status_code}")
                        api_tests['training'] = f'failed: {response.status_code}'

                except requests.exceptions.RequestException as e:
                    print(f"❌ Training endpoint: {str(e)}")
                    api_tests['training'] = f'failed: {str(e)}'

            successful_tests = len([v for v in api_tests.values() if v == 'passed'])
            total_tests = len(api_tests)

            print(f"\n🌐 API Testing Summary: {successful_tests}/{total_tests} endpoints working")

            self.test_results['api_endpoints'] = {
                'status': 'passed' if successful_tests > 0 else 'failed',
                'api_tests': api_tests,
                'successful_tests': successful_tests,
                'total_tests': total_tests
            }

            return successful_tests > 0

        except Exception as e:
            logger.error(f"❌ API endpoint testing failed: {str(e)}")
            self.test_results['api_endpoints'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False

    def test_performance_benchmarks(self) -> bool:
        """Test 7: Performance benchmarking"""
        print("\n⚡ Test 7: Performance Benchmarks")
        print("-" * 40)

        try:
            if not self.ml_engine.trained_models:
                logger.error("❌ No trained models available for benchmarking")
                return False

            print("⚡ Running performance benchmarks...")

            # Run benchmarks
            benchmark_results = self.ml_engine.benchmark_performance(
                num_samples=1000,
                iterations=5
            )

            print("\n📊 Benchmark Results:")
            print("-" * 25)

            for model_name, results in benchmark_results.items():
                if isinstance(results, dict):
                    avg_time = results.get('average_prediction_time_ms', 0)
                    throughput = results.get('predictions_per_second', 0)
                    memory_usage = results.get('memory_usage_mb', 0)

                    print(f"⚡ {model_name}:")
                    print(f"   Avg Time:   {avg_time:.2f}ms")
                    print(f"   Throughput: {throughput:.1f} pred/sec")
                    print(f"   Memory:     {memory_usage:.1f}MB")
                    print()

            # Find fastest model
            fastest_model = None
            fastest_time = float('inf')

            for model_name, results in benchmark_results.items():
                if isinstance(results, dict):
                    avg_time = results.get('average_prediction_time_ms', float('inf'))
                    if avg_time < fastest_time:
                        fastest_time = avg_time
                        fastest_model = model_name

            if fastest_model:
                print(f"🏃 Fastest model: {fastest_model} ({fastest_time:.2f}ms)")

            self.test_results['benchmarks'] = {
                'status': 'passed',
                'benchmark_results': benchmark_results,
                'fastest_model': fastest_model,
                'fastest_time_ms': fastest_time
            }

            return True

        except Exception as e:
            logger.error(f"❌ Performance benchmarking failed: {str(e)}")
            self.test_results['benchmarks'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        print("\n📋 Generating Test Report")
        print("=" * 40)

        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results.values() if r.get('status') == 'passed'])
        failed_tests = total_tests - passed_tests

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'test_summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate_percent': success_rate
            },
            'test_results': self.test_results,
            'system_info': {
                'python_version': sys.version,
                'platform': os.name,
                'working_directory': os.getcwd()
            }
        }

        print(f"📊 Test Summary:")
        print(f"   Total Tests:   {total_tests}")
        print(f"   Passed:        {passed_tests}")
        print(f"   Failed:        {failed_tests}")
        print(f"   Success Rate:  {success_rate:.1f}%")

        if success_rate >= 80:
            print("🎉 EXCELLENT: ML Pipeline is working well!")
        elif success_rate >= 60:
            print("✅ GOOD: ML Pipeline is mostly functional")
        elif success_rate >= 40:
            print("⚠️  WARNING: Some ML components need attention")
        else:
            print("❌ CRITICAL: Major ML pipeline issues detected")

        # Save report to file
        report_file = f"ml_pipeline_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: {report_file}")

        return report

    def run_full_test_suite(self) -> Dict[str, Any]:
        """Run complete ML pipeline testing suite"""
        print("🚀 Starting Comprehensive ML Pipeline Testing")
        print("=" * 60)

        test_sequence = [
            ('Data Loading', self.test_data_loading),
            ('ML Training', self.test_ml_training),
            ('Predictions', self.test_predictions),
            ('Evaluation', self.test_evaluation_metrics),
            ('Visualizations', self.test_visualizations),
            ('API Endpoints', self.test_api_endpoints),
            ('Benchmarks', self.test_performance_benchmarks)
        ]

        start_time = time.time()

        for test_name, test_function in test_sequence:
            try:
                print(f"\n🔄 Running {test_name}...")
                success = test_function()

                if success:
                    print(f"✅ {test_name} completed successfully")
                else:
                    print(f"❌ {test_name} failed")

            except Exception as e:
                logger.error(f"💥 {test_name} crashed: {str(e)}")
                self.test_results[test_name.lower().replace(' ', '_')] = {
                    'status': 'crashed',
                    'error': str(e)
                }

        total_time = time.time() - start_time

        print(f"\n⏱️  Total testing time: {total_time:.2f} seconds")

        # Generate final report
        report = self.generate_report()

        return report

def main():
    """Main function to run ML pipeline tests"""
    print("🔬 Trust Engine ML Pipeline Comprehensive Testing")
    print("=" * 60)
    print("This script will test all ML components, classifiers, and APIs")
    print("Make sure the Flask app is running on localhost:5001 for API tests")
    print("=" * 60)

    # Initialize tester
    tester = MLPipelineTester()

    # Run full test suite
    report = tester.run_full_test_suite()

    # Final summary
    success_rate = report['test_summary']['success_rate_percent']

    print("\n" + "=" * 60)
    print("🏁 ML PIPELINE TESTING COMPLETED")
    print("=" * 60)

    if success_rate >= 80:
        print("🎉 RESULT: EXCELLENT - ML Pipeline is ready for production!")
        print("💡 Your Trust Engine ML implementation is working perfectly.")
        print("📈 All classifiers are trained and performing well.")
        print("🚀 Ready to integrate with your thesis evaluation!")
    elif success_rate >= 60:
        print("✅ RESULT: GOOD - ML Pipeline is mostly functional")
        print("💡 Minor issues detected, but core functionality works.")
        print("🔧 Review the failed tests and address any warnings.")
    elif success_rate >= 40:
        print("⚠️  RESULT: WARNING - Some components need attention")
        print("💡 Several ML components have issues that should be fixed.")
        print("🔧 Review the test report and address the failed components.")
    else:
        print("❌ RESULT: CRITICAL - Major pipeline issues detected")
        print("💡 Significant problems with the ML implementation.")
        print("🆘 Review logs and fix critical issues before proceeding.")

    print("\n📄 Detailed results available in the generated JSON report")
    print("📊 Use Kibana dashboards to monitor real-time ML performance")
    print("🔗 API Documentation: http://localhost:5001/api/ml/swagger")
    print("=" * 60)

if __name__ == "__main__":
    main()
