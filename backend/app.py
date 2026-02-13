"""
Store Provisioning Platform - Backend Control Plane

This is the main Flask application that orchestrates store provisioning.
The backend acts as a control plane, managing store lifecycle via Helm and Kubernetes.

Architecture:
- Database (SQLite): Source of truth for store state
- Helm: Execution engine for provisioning
- Kubernetes: Runtime environment for stores
- Flask API: Interface for dashboard/clients

The backend does NOT:
- Generate Kubernetes YAML
- Implement ecommerce logic
- Manage pods/services directly
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from flask import Flask
from flask_restful import Api
from flask_cors import CORS

from config import Config
from db.session import init_db
from services.store_service import StoreService
from services.helm_service import HelmService
from services.k8s_service import K8sService
from workers.provisioning import ProvisioningWorker
from api.stores import register_resources, init_stores_api

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def setup_logging():
    """Configure logging with file and console handlers."""
    # Create logs directory if it doesn't exist
    log_dir = Path(Config.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture all messages
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # File handler - detailed logging
    log_file_path = log_dir / Config.LOG_FILE
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=Config.LOG_MAX_BYTES,
        backupCount=Config.LOG_BACKUP_COUNT
    )
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    file_formatter = logging.Formatter(Config.LOG_FORMAT)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler - only important messages
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Only INFO and above to console
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Suppress verbose third-party library logging
    # Kubernetes client logs full HTTP responses at DEBUG level
    logging.getLogger('kubernetes.client.rest').setLevel(logging.WARNING)
    logging.getLogger('kubernetes').setLevel(logging.INFO)
    # Suppress urllib3 connection pool logging
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Log the log file location
    root_logger.info(f"Logging to file: {log_file_path}")


# Configure logging
setup_logging()
logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    """
    Create and configure the Flask application.
    
    This function:
    1. Initializes the database
    2. Creates service instances
    3. Starts the provisioning worker
    4. Registers API blueprints
    5. Handles crash recovery (resumes PROVISIONING stores)
    
    Returns:
        Configured Flask app
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Enable CORS for all routes
    CORS(app)
    
    # Initialize Flask-RESTful API
    api = Api(app, prefix='/api/v1')
    
    logger.info("Initializing Store Provisioning Platform Backend...")
    
    # Initialize database
    init_db()
    logger.info(f"Database initialized")
    
    # Initialize services
    helm_service = HelmService()
    
    k8s_service = K8sService()
    
    store_service = StoreService()
    
    logger.info("All services initialized successfully")
    
    # Initialize provisioning worker
    provisioning_worker = ProvisioningWorker(
        helm_service=helm_service,
        k8s_service=k8s_service,
        store_service=store_service,
    )
    
    provisioning_worker.start()
    logger.info("ProvisioningWorker started")
    
    # Crash recovery: Resume provisioning for stores in PROVISIONING state
    logger.info("Checking for stores to resume...")
    provisioning_worker.resume_provisioning_stores()
    
    # Register REST resources    
    # Initialize stores API with dependencies
    init_stores_api(
        store_service=store_service,
        helm_service=helm_service,
        provisioning_worker=provisioning_worker
    )
    
    # Register all REST resources
    register_resources(api)
    logger.info("REST API resources registered")
    
    return app


def main():
    app = create_app()
    
    # Get configuration from Config class
    host = Config.FLASK_HOST
    port = Config.FLASK_PORT
    debug = Config.FLASK_DEBUG
    
    logger.info(f"Starting Flask application on {host}:{port} (debug={debug})")
    
    # Run application
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()
