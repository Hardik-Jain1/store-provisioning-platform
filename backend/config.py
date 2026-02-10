"""
Configuration for the Store Provisioning Platform Backend

This module defines all configuration parameters for the backend control plane.
Values can be overridden via environment variables for different deployment scenarios.
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

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

# Domain configuration
BASE_DOMAIN = os.getenv('BASE_DOMAIN', 'localhost')

# Flask configuration
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
