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

import os
import logging
from flask import Flask
from flask_restful import Api
from flask_cors import CORS

from config import Config
from db.session import init_db, get_session
from models.store import Store
from services.store_service import StoreService
from services.helm_service import HelmService
from services.k8s_service import K8sService
from workers.provisioning import ProvisioningWorker
from api.stores import register_resources, init_stores_api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
    logger.info("✓ ProvisioningWorker started")
    
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
    
    # Get configuration
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Flask application on {host}:{port} (debug={debug})")
    
    # Run application
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()
