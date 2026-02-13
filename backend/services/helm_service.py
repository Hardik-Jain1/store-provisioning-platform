"""
Helm Service

Responsible for all Helm CLI interactions.
This service ONLY invokes Helm commands; it does not generate YAML or templates.
"""

import subprocess
import logging
from typing import Dict, Optional
from pathlib import Path

from config import Config

logger = logging.getLogger(__name__)


class HelmService:
    """
    Service for interacting with Helm CLI.
    
    The backend treats Helm as a black box executor.
    All templating and manifest generation is Helm's responsibility.
    """
    
    def __init__(self, chart_path: Optional[str] = None):
        """
        Initialize Helm service.
        
        Args:
            chart_path: Path to Helm chart directory (defaults to config value)
        """
        self.chart_path = chart_path or Config.HELM_CHART_PATH
        logger.info(f"HelmService initialized with chart path: {self.chart_path}")
        
        # Verify Helm is available
        self._verify_helm_available()
        
        # Verify chart exists
        self._verify_chart_exists()
    
    def _verify_helm_available(self):
        """Verify Helm CLI is available on the system."""
        try:
            result = subprocess.run(
                ['helm', 'version', '--short'],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"Helm version: {result.stdout.strip()}")
        except FileNotFoundError:
            raise RuntimeError("Helm CLI not found. Please install Helm.")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Helm CLI error: {e.stderr}")
    
    def _verify_chart_exists(self):
        """Verify the Helm chart directory exists."""
        chart_path = Path(self.chart_path)
        if not chart_path.exists():
            raise RuntimeError(f"Helm chart not found at: {self.chart_path}")
        
        chart_yaml = chart_path / 'Chart.yaml'
        if not chart_yaml.exists():
            raise RuntimeError(f"Chart.yaml not found in: {self.chart_path}")
        
        logger.info(f"Helm chart validated at: {self.chart_path}")
    
    def install(
        self,
        release_name: str,
        namespace: str,
        values: Dict[str, str]
    ) -> tuple[bool, str]:
        """
        Install a Helm release.
        
        This is the PRIMARY interaction with Kubernetes. The backend does not
        create resources directly; it delegates to Helm.
        
        Args:
            release_name: Helm release name (must be deterministic = store ID)
            namespace: Kubernetes namespace (must be deterministic = store-{id})
            values: Dynamic values to pass via --set
        
        Returns:
            Tuple of (success: bool, output: str)
        """
        logger.info(f"Installing Helm release: {release_name} in namespace: {namespace}")
        
        # Build Helm install command
        cmd = [
            'helm', 'install', release_name,
            self.chart_path,
            '--namespace', namespace,
            '--create-namespace',
            '-f', f'{self.chart_path}/{Config.HELM_VALUES_FILE}',
            '-f', f'{self.chart_path}/{Config.HELM_ENV_VALUES_FILE}',
        ]
        
        # Add dynamic values via --set
        for key, value in values.items():
            cmd.extend(['--set', f'{key}={value}'])
        
        logger.debug(f"Helm command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=300  # 5 minute timeout for Helm install
            )
            
            logger.info(f"Helm install succeeded for release: {release_name}")
            # logger.debug(f"Helm output: {result.stdout}")
            
            return True, result.stdout
            
        except subprocess.TimeoutExpired:
            error_msg = f"Helm install timed out for release: {release_name}"
            logger.error(error_msg)
            return False, error_msg
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Helm install failed: {e.stderr}"
            logger.error(f"Helm install failed for release {release_name}: {e.stderr}")
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error during Helm install: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def uninstall(self, release_name: str, namespace: str) -> tuple[bool, str]:
        """
        Uninstall a Helm release.
        
        This triggers clean teardown of all resources created by the release.
        Because we use namespace-per-store, this is safe and complete.
        
        Args:
            release_name: Helm release name
            namespace: Kubernetes namespace
        
        Returns:
            Tuple of (success: bool, output: str)
        """
        logger.info(f"Uninstalling Helm release: {release_name} from namespace: {namespace}")
        
        cmd = [
            'helm', 'uninstall', release_name,
            '--namespace', namespace
        ]
        
        logger.debug(f"Helm command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=120  # 2 minute timeout for uninstall
            )
            
            logger.info(f"Helm uninstall succeeded for release: {release_name}")
            logger.debug(f"Helm output: {result.stdout}")
            
            return True, result.stdout
            
        except subprocess.TimeoutExpired:
            error_msg = f"Helm uninstall timed out for release: {release_name}"
            logger.error(error_msg)
            return False, error_msg
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Helm uninstall failed: {e.stderr}"
            logger.error(f"Helm uninstall failed for release {release_name}: {e.stderr}")
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error during Helm uninstall: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_release_status(self, release_name: str, namespace: str) -> Optional[str]:
        """
        Get the status of a Helm release.
        
        Args:
            release_name: Helm release name
            namespace: Kubernetes namespace
        
        Returns:
            Status string or None if release not found
        """
        cmd = [
            'helm', 'status', release_name,
            '--namespace', namespace,
            '--output', 'json'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
            
            import json
            status_data = json.loads(result.stdout)
            return status_data.get('info', {}).get('status')
            
        except subprocess.CalledProcessError:
            # Release not found
            return None
        except Exception as e:
            logger.warning(f"Failed to get release status: {e}")
            return None
