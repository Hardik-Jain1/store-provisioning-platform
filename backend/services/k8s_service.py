"""
Kubernetes Service

Responsible for polling Kubernetes API to check readiness of store resources.
This service is READ-ONLY; it never creates or modifies Kubernetes resources.
"""

import logging
from typing import Optional, Dict
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from config import KUBECONFIG_PATH

logger = logging.getLogger(__name__)


class K8sService:
    """
    Service for interacting with Kubernetes API.
    
    This service ONLY reads Kubernetes state to determine provisioning success.
    It never creates, updates, or deletes resources (that's Helm's job).
    """
    
    def __init__(self):
        """Initialize Kubernetes client."""
        self._load_kube_config()
        
        # Initialize API clients
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.batch_v1 = client.BatchV1Api()
        self.networking_v1 = client.NetworkingV1Api()
        
        logger.info("K8sService initialized successfully")
    
    def _load_kube_config(self):
        """Load Kubernetes configuration."""
        try:
            if KUBECONFIG_PATH:
                config.load_kube_config(config_file=KUBECONFIG_PATH)
                logger.info(f"Loaded kubeconfig from: {KUBECONFIG_PATH}")
            else:
                config.load_kube_config()
                logger.info("Loaded kubeconfig from default location")
        except Exception as e:
            logger.error(f"Failed to load kubeconfig: {e}")
            raise RuntimeError(f"Failed to load Kubernetes config: {e}")
    
    def check_namespace_exists(self, namespace: str) -> bool:
        """
        Check if a namespace exists.
        
        Args:
            namespace: Namespace name
        
        Returns:
            True if namespace exists, False otherwise
        """
        try:
            self.core_v1.read_namespace(name=namespace)
            return True
        except ApiException as e:
            if e.status == 404:
                return False
            logger.error(f"Error checking namespace {namespace}: {e}")
            raise
    
    def check_pods_ready(self, namespace: str) -> tuple[bool, str]:
        """
        Check if all pods in a namespace are ready.
        
        A pod is considered ready when:
        - Phase is 'Running' or 'Succeeded'
        - All containers are ready
        - No containers are in CrashLoopBackOff
        
        Args:
            namespace: Namespace to check
        
        Returns:
            Tuple of (all_ready: bool, status_message: str)
        """
        try:
            pods = self.core_v1.list_namespaced_pod(namespace=namespace)
            
            if not pods.items:
                return False, "No pods found in namespace"
            
            pod_statuses = []
            all_ready = True
            
            for pod in pods.items:
                pod_name = pod.metadata.name
                phase = pod.status.phase
                
                # Check if pod is in a terminal failure state
                if phase in ['Failed', 'Unknown']:
                    all_ready = False
                    pod_statuses.append(f"{pod_name}: {phase}")
                    continue
                
                # Check for CrashLoopBackOff or ImagePullBackOff
                if pod.status.container_statuses:
                    for container in pod.status.container_statuses:
                        if container.state.waiting:
                            reason = container.state.waiting.reason
                            if reason in ['CrashLoopBackOff', 'ImagePullBackOff', 'ErrImagePull']:
                                all_ready = False
                                pod_statuses.append(f"{pod_name}/{container.name}: {reason}")
                                continue
                
                # Check if pod is ready
                if pod.status.conditions:
                    ready_condition = next(
                        (c for c in pod.status.conditions if c.type == 'Ready'),
                        None
                    )
                    
                    if ready_condition and ready_condition.status == 'True':
                        pod_statuses.append(f"{pod_name}: Ready")
                    else:
                        all_ready = False
                        reason = ready_condition.reason if ready_condition else 'Unknown'
                        pod_statuses.append(f"{pod_name}: Not Ready ({reason})")
                else:
                    all_ready = False
                    pod_statuses.append(f"{pod_name}: No conditions")
            
            status_message = "; ".join(pod_statuses)
            
            if all_ready:
                logger.info(f"All pods ready in namespace {namespace}")
            else:
                logger.debug(f"Pods not ready in namespace {namespace}: {status_message}")
            
            return all_ready, status_message
            
        except ApiException as e:
            if e.status == 404:
                return False, f"Namespace {namespace} not found"
            logger.error(f"Error checking pods in namespace {namespace}: {e}")
            return False, f"API error: {e.reason}"
    
    def check_job_succeeded(self, namespace: str, job_name_prefix: str = 'setup-job') -> tuple[bool, Optional[str]]:
        """
        Check if a setup job has succeeded.
        
        The setup job is responsible for initializing the store
        (e.g., installing WooCommerce plugins, seeding data).
        
        Args:
            namespace: Namespace to check
            job_name_prefix: Prefix of job name to look for
        
        Returns:
            Tuple of (succeeded: bool, failure_reason: Optional[str])
        """
        try:
            jobs = self.batch_v1.list_namespaced_job(namespace=namespace)
            
            # Find the setup job
            setup_job = None
            for job in jobs.items:
                if job.metadata.name.startswith(job_name_prefix):
                    setup_job = job
                    break
            
            if not setup_job:
                # Job might not be created yet
                return False, None
            
            job_status = setup_job.status
            
            # Check if job succeeded
            if job_status.succeeded and job_status.succeeded > 0:
                logger.info(f"Setup job succeeded in namespace {namespace}")
                return True, None
            
            # Check if job failed
            if job_status.failed and job_status.failed > 0:
                failure_reason = f"Setup job failed ({job_status.failed} attempts)"
                logger.warning(f"{failure_reason} in namespace {namespace}")
                return False, failure_reason
            
            # Job is still running
            return False, None
            
        except ApiException as e:
            if e.status == 404:
                return False, None  # Job not created yet
            logger.error(f"Error checking job in namespace {namespace}: {e}")
            return False, f"API error: {e.reason}"
    
    def get_ingress_url(self, namespace: str, ingress_name: str = 'store-ingress') -> Optional[str]:
        """
        Get the URL for a store's ingress.
        
        Args:
            namespace: Namespace to check
            ingress_name: Name of the ingress resource
        
        Returns:
            Store URL if available, None otherwise
        """
        try:
            ingress = self.networking_v1.read_namespaced_ingress(
                name=ingress_name,
                namespace=namespace
            )
            
            # Get the first host from ingress rules
            if ingress.spec.rules and len(ingress.spec.rules) > 0:
                host = ingress.spec.rules[0].host
                
                # Determine protocol (check for TLS)
                protocol = 'https' if ingress.spec.tls else 'http'
                
                url = f"{protocol}://{host}"
                logger.info(f"Ingress URL for {namespace}: {url}")
                return url
            
            logger.warning(f"No ingress rules found for {ingress_name} in {namespace}")
            return None
            
        except ApiException as e:
            if e.status == 404:
                logger.debug(f"Ingress {ingress_name} not found in namespace {namespace}")
                return None
            logger.error(f"Error getting ingress in namespace {namespace}: {e}")
            return None
    
    def check_store_ready(self, namespace: str) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Comprehensive readiness check for a store.
        
        Checks:
        1. All pods are ready
        2. Setup job has succeeded
        3. Ingress is available
        
        Args:
            namespace: Namespace to check
        
        Returns:
            Tuple of (ready: bool, store_url: Optional[str], failure_reason: Optional[str])
        """
        logger.debug(f"Checking readiness for namespace: {namespace}")
        
        # Check namespace exists
        if not self.check_namespace_exists(namespace):
            return False, None, f"Namespace {namespace} does not exist"
        
        # Check pods
        pods_ready, pod_status = self.check_pods_ready(namespace)
        if not pods_ready:
            return False, None, f"Pods not ready: {pod_status}"
        
        # Check setup job
        job_succeeded, job_failure = self.check_job_succeeded(namespace)
        if not job_succeeded:
            if job_failure:
                return False, None, job_failure
            # Job still running, not ready yet
            return False, None, None
        
        # Check ingress
        store_url = self.get_ingress_url(namespace)
        if not store_url:
            return False, None, "Ingress URL not available"
        
        # All checks passed
        logger.info(f"Store ready in namespace {namespace}: {store_url}")
        return True, store_url, None
