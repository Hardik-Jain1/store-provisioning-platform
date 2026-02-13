"""
Configuration for the Store Provisioning Platform Backend

This module defines all configuration parameters for the backend control plane.
Values can be overridden via environment variables for different deployment scenarios.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()


class Config:
    """Configuration class for the Store Provisioning Platform"""
    
    # Base directory
    BASE_DIR = Path(__file__).parent
    
    # Logging configuration
    LOG_DIR = os.getenv('LOG_DIR', str(BASE_DIR / 'logs'))
    LOG_FILE = os.getenv('LOG_FILE', 'store_platform.log')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))
    
    # Database configuration
    DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR}/store_platform.db')

    # Helm configuration
    HELM_CHART_PATH = os.getenv('HELM_CHART_PATH', str(BASE_DIR.parent / 'helm' / 'store'))
    HELM_VALUES_FILE = os.getenv('HELM_VALUES_FILE', 'values.yaml')
    HELM_ENV_VALUES_FILE = os.getenv('HELM_ENV_VALUES_FILE', 'values-local.yaml')

    # Kubernetes configuration
    # Default to current kubeconfig context
    KUBECONFIG_PATH = os.getenv('KUBECONFIG', None)

    # Provisioning configuration
    PROVISIONING_TIMEOUT_SECONDS = int(os.getenv('PROVISIONING_TIMEOUT_SECONDS', 600))  # 10 minutes
    PROVISIONING_POLL_INTERVAL_SECONDS = int(os.getenv('PROVISIONING_POLL_INTERVAL_SECONDS', 5))
    PROVISIONING_MAX_WORKERS = int(os.getenv('PROVISIONING_MAX_WORKERS', 5))  # Max concurrent provisioning tasks

    # Domain configuration
    BASE_DOMAIN = os.getenv('BASE_DOMAIN', 'localhost')

    # Flask configuration
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
