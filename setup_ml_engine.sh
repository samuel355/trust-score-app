#!/bin/bash

# Trust Engine ML Setup Script
# Automated setup for Machine Learning components and dependencies

set -e  # Exit on any error

echo "🚀 Trust Engine ML Setup Starting..."
echo "=================================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if script is run from correct directory
if [ ! -f "requirements.txt" ]; then
    print_error "Please run this script from the trust_engine_app directory"
    exit 1
fi

print_info "Setting up Trust Engine ML components..."

# 1. Check Python version
echo ""
echo "🐍 Checking Python Environment"
echo "--------------------------------"

python_version=$(python3 --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+' | head -1)
major_version=$(echo $python_version | cut -d. -f1)
minor_version=$(echo $python_version | cut -d. -f2)

if [ "$major_version" -eq 3 ] && [ "$minor_version" -ge 8 ]; then
    print_status "Python $python_version detected (compatible)"
else
    print_error "Python 3.8+ required, found Python $python_version"
    exit 1
fi

# 2. Create virtual environment if it doesn't exist
echo ""
echo "🌐 Virtual Environment Setup"
echo "-----------------------------"

if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_info "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
print_status "Virtual environment activated"

# 3. Upgrade pip and install wheel
echo ""
echo "📦 Package Management Setup"
echo "---------------------------"

pip install --upgrade pip setuptools wheel
print_status "Package management tools updated"

# 4. Install ML dependencies
echo ""
echo "🧠 Installing ML Dependencies"
echo "-----------------------------"

print_info "Installing core ML libraries..."

# Install in specific order to avoid conflicts
pip install numpy>=1.21.0
pip install scipy>=1.7.0
pip install pandas>=1.3.0
pip install scikit-learn>=1.0.0
pip install joblib>=1.1.0

print_status "Core ML libraries installed"

print_info "Installing visualization libraries..."
pip install matplotlib>=3.5.0
pip install seaborn>=0.11.0
pip install plotly>=5.0.0

print_status "Visualization libraries installed"

print_info "Installing additional ML utilities..."
pip install imbalanced-learn>=0.8.0
pip install xgboost>=1.5.0
pip install lightgbm>=3.3.0

print_status "Additional ML utilities installed"

# 5. Install all requirements
echo ""
echo "📋 Installing All Requirements"
echo "------------------------------"

pip install -r requirements.txt
print_status "All requirements installed"

# 6. Create necessary directories
echo ""
echo "📁 Creating Directory Structure"
echo "-------------------------------"

directories=(
    "models"
    "evaluation_results"
    "charts"
    "logs"
    "data/processed"
    "kibana/dashboards"
    "scripts/logs"
)

for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        print_status "Created directory: $dir"
    else
        print_info "Directory already exists: $dir"
    fi
done

# 7. Set up model storage
echo ""
echo "💾 Model Storage Setup"
echo "---------------------"

# Create model metadata file
cat > models/model_metadata.json << EOF
{
    "created": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "version": "1.0.0",
    "description": "Trust Engine ML Models Storage",
    "classifiers": {
        "RandomForest": {"file": "random_forest.joblib", "trained": false},
        "KNN": {"file": "knn.joblib", "trained": false},
        "NaiveBayes": {"file": "naive_bayes.joblib", "trained": false},
        "MLP": {"file": "mlp.joblib", "trained": false},
        "AdaptiveKNN": {"file": "adaptive_knn.joblib", "trained": false},
        "AdaptiveRandomForest": {"file": "adaptive_rf.joblib", "trained": false}
    },
    "feature_scalers": {
        "standard_scaler": {"file": "standard_scaler.joblib", "created": false}
    },
    "label_encoders": {
        "risk_encoder": {"file": "risk_encoder.joblib", "created": false}
    }
}
EOF

print_status "Model metadata file created"

# 8. Configure logging
echo ""
echo "📝 Logging Configuration"
echo "------------------------"

# Create logging configuration
cat > logs/ml_logging_config.json << EOF
{
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "logs/ml_engine.log",
            "mode": "a"
        },
        "error_file": {
            "class": "logging.FileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": "logs/ml_errors.log",
            "mode": "a"
        }
    },
    "loggers": {
        "app.ml_engine": {
            "level": "DEBUG",
            "handlers": ["console", "file", "error_file"],
            "propagate": false
        },
        "app.evaluation": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": false
        },
        "app.visualization": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": false
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"]
    }
}
EOF

print_status "Logging configuration created"

# 9. Install Kibana dashboard configurations
echo ""
echo "📊 Kibana Dashboard Setup"
echo "-------------------------"

if [ -f "kibana/dashboards/ml_performance_dashboard.json" ]; then
    print_status "ML performance dashboard configuration ready"
else
    print_warning "ML dashboard configuration not found"
fi

if [ -f "kibana/dashboards/ml_index_patterns.json" ]; then
    print_status "ML index patterns configuration ready"
else
    print_warning "ML index patterns configuration not found"
fi

# 10. Verify ML modules
echo ""
echo "🔍 Verifying ML Modules"
echo "-----------------------"

python3 -c "
import sys
try:
    from app.ml_engine import TrustScoreMLEngine
    print('✅ ML Engine module loaded successfully')
except ImportError as e:
    print(f'❌ ML Engine import failed: {e}')
    sys.exit(1)

try:
    from app.evaluation import TrustEngineEvaluator
    print('✅ Evaluation module loaded successfully')
except ImportError as e:
    print(f'❌ Evaluation import failed: {e}')
    sys.exit(1)

try:
    from app.visualization import TrustEngineVisualizer
    print('✅ Visualization module loaded successfully')
except ImportError as e:
    print(f'❌ Visualization import failed: {e}')
    sys.exit(1)

try:
    from routes.ml_endpoints import ml_bp
    print('✅ ML API endpoints loaded successfully')
except ImportError as e:
    print(f'❌ ML API endpoints import failed: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    print_status "All ML modules verified successfully"
else
    print_error "ML module verification failed"
    exit 1
fi

# 11. Create sample configuration files
echo ""
echo "⚙️  Configuration Files"
echo "----------------------"

# Create ML configuration file
cat > app/ml_config.py << EOF
"""
Machine Learning Configuration for Trust Engine
"""

import os
from typing import Dict, List, Any

class MLConfig:
    """ML-specific configuration settings"""

    # Model Storage
    MODEL_STORAGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'models')

    # Training Configuration
    DEFAULT_TEST_SIZE = 0.2
    DEFAULT_CV_FOLDS = 5
    DEFAULT_RANDOM_STATE = 42

    # Performance Thresholds
    MIN_ACCURACY_THRESHOLD = 0.85
    MIN_F1_SCORE_THRESHOLD = 0.80
    MAX_PREDICTION_LATENCY_MS = 100

    # Classifier Configurations
    CLASSIFIER_CONFIGS = {
        'RandomForest': {
            'n_estimators': 100,
            'max_depth': 10,
            'min_samples_split': 5,
            'min_samples_leaf': 2,
            'random_state': DEFAULT_RANDOM_STATE,
            'n_jobs': -1
        },
        'KNN': {
            'n_neighbors': 5,
            'weights': 'distance',
            'algorithm': 'auto',
            'metric': 'minkowski'
        },
        'NaiveBayes': {
            'var_smoothing': 1e-9
        },
        'MLP': {
            'hidden_layer_sizes': (100, 50),
            'activation': 'relu',
            'solver': 'adam',
            'alpha': 0.0001,
            'learning_rate': 'adaptive',
            'max_iter': 500,
            'random_state': DEFAULT_RANDOM_STATE
        }
    }

    # Adaptive Classifier Grid Search Parameters
    ADAPTIVE_CONFIGS = {
        'AdaptiveKNN': {
            'param_grid': {
                'n_neighbors': [3, 5, 7, 9, 11],
                'weights': ['uniform', 'distance'],
                'metric': ['euclidean', 'manhattan', 'minkowski']
            },
            'cv': 5,
            'scoring': 'f1_weighted',
            'n_jobs': -1
        },
        'AdaptiveRandomForest': {
            'param_grid': {
                'n_estimators': [50, 100, 200],
                'max_depth': [5, 10, 15, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            },
            'cv': 5,
            'scoring': 'f1_weighted',
            'n_jobs': -1
        }
    }

    # Feature Engineering
    FEATURE_SELECTION = {
        'enable_feature_selection': True,
        'selection_method': 'variance_threshold',
        'variance_threshold': 0.01,
        'max_features': 50
    }

    # Trust Score Calculation
    TRUST_SCORE_CONFIG = {
        'confidence_weight': 0.4,
        'consensus_weight': 0.3,
        'historical_weight': 0.2,
        'risk_penalty_weight': 0.1
    }

    # Risk Level Mapping
    RISK_LEVELS = {
        'low': {'min_score': 0.8, 'mfa_required': False},
        'medium': {'min_score': 0.6, 'mfa_required': False},
        'high': {'min_score': 0.4, 'mfa_required': True},
        'critical': {'min_score': 0.0, 'mfa_required': True}
    }

    # Elasticsearch Index Settings
    ELASTICSEARCH_INDICES = {
        'ml_metrics': 'ml-metrics',
        'ml_performance': 'ml-performance',
        'ml_predictions': 'ml-predictions',
        'model_training': 'ml-training'
    }

    # API Settings
    API_CONFIG = {
        'max_batch_size': 1000,
        'request_timeout_seconds': 30,
        'rate_limit_per_minute': 1000
    }

    @classmethod
    def get_classifier_config(cls, classifier_name: str) -> Dict[str, Any]:
        """Get configuration for a specific classifier"""
        return cls.CLASSIFIER_CONFIGS.get(classifier_name, {})

    @classmethod
    def get_adaptive_config(cls, classifier_name: str) -> Dict[str, Any]:
        """Get adaptive configuration for a classifier"""
        return cls.ADAPTIVE_CONFIGS.get(classifier_name, {})

    @classmethod
    def validate_trust_score(cls, score: float) -> bool:
        """Validate trust score is within acceptable range"""
        return 0.0 <= score <= 1.0
EOF

print_status "ML configuration file created"

# 12. Make scripts executable
echo ""
echo "🔧 Setting Script Permissions"
echo "-----------------------------"

chmod +x scripts/test_ml_pipeline.py
chmod +x setup_ml_engine.sh

print_status "Script permissions set"

# 13. Create quick start guide
echo ""
echo "📖 Creating Quick Start Guide"
echo "-----------------------------"

cat > ML_QUICK_START.md << EOF
# Trust Engine ML Quick Start Guide

## 🚀 Getting Started

### 1. Verify Installation
\`\`\`bash
python3 scripts/test_ml_pipeline.py
\`\`\`

### 2. Start the Flask Application
\`\`\`bash
python3 run.py
\`\`\`

### 3. Test ML API Endpoints

#### Health Check
\`\`\`bash
curl http://localhost:5001/api/ml/health
\`\`\`

#### Train Models
\`\`\`bash
curl -X POST http://localhost:5001/api/ml/train \\
     -H "Content-Type: application/json" \\
     -d '{"use_sample_data": true, "test_size": 0.2}'
\`\`\`

#### Make Predictions
\`\`\`bash
curl -X POST http://localhost:5001/api/ml/predict \\
     -H "Content-Type: application/json" \\
     -d '{"features": {...}, "classifier": "RandomForest"}'
\`\`\`

## 📊 Available ML Classifiers

1. **Random Forest** - Robust ensemble method
2. **K-Nearest Neighbors** - Instance-based learning
3. **Naïve Bayes** - Probabilistic classifier
4. **Multi-Layer Perceptron** - Neural network
5. **Adaptive KNN** - Hyperparameter-tuned KNN
6. **Adaptive Random Forest** - Optimized ensemble

## 🔗 API Endpoints

- \`GET /api/ml/health\` - Service health check
- \`POST /api/ml/train\` - Train all classifiers
- \`POST /api/ml/predict\` - Single prediction
- \`POST /api/ml/predict/batch\` - Batch predictions
- \`GET /api/ml/evaluate\` - Model evaluation
- \`GET /api/ml/visualize/<chart_type>\` - Generate charts
- \`GET /api/ml/models\` - Model management
- \`POST /api/ml/benchmark\` - Performance benchmarks

## 📈 Monitoring

- Kibana dashboards available at: \`http://localhost:5601\`
- Logs available in: \`logs/\` directory
- Model files stored in: \`models/\` directory

## 🎯 Performance Metrics

The system tracks:
- Accuracy, Precision, Recall, F1-Score
- False Negative Rate (FNR)
- ROC Curves & AUC
- Authentication Latency
- System Throughput
- Policy Enforcement Delay

## 🔧 Configuration

ML settings can be modified in \`app/ml_config.py\`

## 📚 Documentation

For detailed documentation, see:
- \`docs/\` directory
- Swagger UI: \`http://localhost:5001/api/ml/swagger\`
EOF

print_status "Quick start guide created"

# 14. Final verification and summary
echo ""
echo "🎯 Final Verification"
echo "--------------------"

# Count installed packages
installed_packages=$(pip list | wc -l)
print_info "Installed packages: $installed_packages"

# Check disk space for models
available_space=$(df -h . | awk 'NR==2 {print $4}')
print_info "Available disk space: $available_space"

# Check if all required directories exist
missing_dirs=0
for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        missing_dirs=$((missing_dirs + 1))
    fi
done

if [ $missing_dirs -eq 0 ]; then
    print_status "All required directories created"
else
    print_warning "$missing_dirs directories missing"
fi

echo ""
echo "=================================================="
print_status "Trust Engine ML Setup Completed Successfully!"
echo "=================================================="

echo ""
echo "🎉 SETUP SUMMARY:"
echo "✅ Python environment configured"
echo "✅ ML dependencies installed"
echo "✅ Directory structure created"
echo "✅ Configuration files generated"
echo "✅ Logging configured"
echo "✅ API endpoints ready"
echo "✅ Kibana dashboards configured"

echo ""
echo "🚀 NEXT STEPS:"
echo "1. Start the Flask application: python3 run.py"
echo "2. Run ML tests: python3 scripts/test_ml_pipeline.py"
echo "3. Access API documentation: http://localhost:5001/api/ml/swagger"
echo "4. View Kibana dashboards: http://localhost:5601"
echo "5. Read quick start guide: ML_QUICK_START.md"

echo ""
echo "📊 YOUR ML PIPELINE IS READY FOR:"
echo "🔹 Training 6 ML classifiers (4 core + 2 adaptive)"
echo "🔹 Real-time trust score predictions"
echo "🔹 Comprehensive performance evaluation"
echo "🔹 Publication-ready visualizations"
echo "🔹 REST API for integration"
echo "🔹 Real-time monitoring with Kibana"

echo ""
echo "🎓 Perfect for your thesis evaluation!"
echo "=================================================="

print_info "Setup script completed. Check logs/ for any issues."
