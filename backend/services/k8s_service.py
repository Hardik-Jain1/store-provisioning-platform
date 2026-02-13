"""
Kubernetes Service

Responsible for polling Kubernetes API to check readiness of store resources.
This service is READ-ONLY; it never creates or modifies Kubernetes resources.
"""

import logging
from typing import Optional, Dict
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from config import Config

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
            if Config.KUBECONFIG_PATH:
                config.load_kube_config(config_file=Config.KUBECONFIG_PATH)
                logger.info(f"Loaded kubeconfig from: {Config.KUBECONFIG_PATH}")
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
    
    def check_pods_ready(self, namespace: str) -> tuple[bool, str, bool]:
        """
        Check pod readiness status.
        
        Returns:
            Tuple of (all_ready: bool, status_message: str, setup_job_completed: bool)
        """
        try:
            pods = self.core_v1.list_namespaced_pod(namespace=namespace)
            
            mysql_ready = False
            wordpress_ready = False
            setup_job_completed = False
            failure_reason = None
            pod_statuses = []
            
            for pod in pods.items:
                name = pod.metadata.name
                status = pod.status.phase
                
                # Count ready containers
                ready_count = 0
                total_containers = 0
                if pod.status.container_statuses:
                    for container in pod.status.container_statuses:
                        total_containers += 1
                        if container.ready:
                            ready_count += 1
                ready = f"{ready_count}/{total_containers}"
                
                # Get restarts
                restarts = 0
                if pod.status.container_statuses:
                    for container in pod.status.container_statuses:
                        restarts += container.restart_count
                
                # Identify pod type and check status
                if 'mysql' in name:
                    # MySQL pod check
                    if status == 'Running' and ready_count == total_containers:
                        mysql_ready = True
                        pod_statuses.append(f"{name}: Ready (1/1)")
                    elif status == 'Pending':
                        pod_statuses.append(f"{name}: Pending")
                    else:
                        # Check for failure reasons
                        if pod.status.container_statuses:
                            container = pod.status.container_statuses[0]
                            if container.state.waiting:
                                reason = container.state.waiting.reason
                                if reason in ['ImagePullBackOff', 'ErrImagePull']:
                                    failure_reason = f"MySQL: {reason}"
                                elif reason == 'CrashLoopBackOff':
                                    failure_reason = f"MySQL: CrashLoopBackOff"
                                else:
                                    pod_statuses.append(f"{name}: {reason}")
                            elif container.state.terminated:
                                failure_reason = f"MySQL: Container terminated"
                
                elif 'wordpress' in name:
                    # WordPress pod check
                    if status == 'Running' and ready_count == total_containers:
                        wordpress_ready = True
                        pod_statuses.append(f"{name}: Ready (1/1)")
                    elif status == 'Pending':
                        pod_statuses.append(f"{name}: Pending")
                    else:
                        # Check for failure reasons
                        if pod.status.container_statuses:
                            container = pod.status.container_statuses[0]
                            if container.state.waiting:
                                reason = container.state.waiting.reason
                                if reason in ['ImagePullBackOff', 'ErrImagePull']:
                                    failure_reason = f"WordPress: {reason}"
                                elif reason == 'CrashLoopBackOff':
                                    failure_reason = f"WordPress: CrashLoopBackOff (Restarts: {restarts})"
                                else:
                                    pod_statuses.append(f"{name}: {reason}")
                            elif container.state.terminated:
                                failure_reason = f"WordPress: Container terminated"
                
                elif 'woocommerce-setup' in name:
                    # Setup job pod check
                    if pod.status.container_statuses:
                        container = pod.status.container_statuses[0]
                        
                        if container.state.terminated:
                            # Job completed
                            if container.state.terminated.exit_code == 0:
                                setup_job_completed = True
                                pod_statuses.append(f"{name}: Completed")
                            else:
                                failure_reason = f"Setup job failed with exit code {container.state.terminated.exit_code}"
                        elif container.state.running:
                            pod_statuses.append(f"{name}: Running (0/1)")
                        elif container.state.waiting:
                            reason = container.state.waiting.reason
                            pod_statuses.append(f"{name}: {reason}")
            
            # Determine overall readiness
            status_msg = " | ".join(pod_statuses)
            
            # All ready only if MySQL and WordPress are ready AND setup job is completed
            all_ready = mysql_ready and wordpress_ready and setup_job_completed
            
            return all_ready, status_msg, failure_reason
            
        except ApiException as e:
            if e.status == 404:
                return False, f"Namespace {namespace} not found", None
            logger.error(f"Error checking pods: {e}")
            return False, f"API error: {e.reason}", None
    
    def get_ingress_url(self, namespace: str, ingress_name: str) -> Optional[str]:
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
    
    def check_store_ready(self, namespace: str, ingress: str) -> tuple[bool, Optional[str], Optional[str]]:
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
        all_ready, pod_status, failure_reason = self.check_pods_ready(namespace)
        logger.debug(f"Pod status for {namespace}: {pod_status}")

        if failure_reason:
            return False, None, failure_reason
        
        if not all_ready:
            # Still provisioning, no failure
            return False, None, None
        
        # All pods ready, get ingress URL
        store_url = self.get_ingress_url(namespace, ingress)
        return True, store_url, None
