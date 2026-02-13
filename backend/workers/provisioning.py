"""
Provisioning Worker

Handles asynchronous provisioning of stores.
Uses ThreadPoolExecutor for concurrent provisioning of multiple stores.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional, Dict

from models.store import Store
from services.helm_service import HelmService
from services.k8s_service import K8sService
from services.store_service import StoreService
from config import Config

logger = logging.getLogger(__name__)


class ProvisioningWorker:
    """
    Background worker for asynchronous store provisioning using ThreadPoolExecutor.
    
    This worker:
    1. Maintains a thread pool for concurrent provisioning
    2. Invokes Helm to install releases
    3. Polls Kubernetes to check readiness
    4. Updates database with status
    5. Enforces timeouts and concurrency limits
    
    The worker is crash-safe: if it dies, stores remain in PROVISIONING state
    and will be resumed on backend restart.
    """
    
    def __init__(
        self,
        helm_service: HelmService,
        k8s_service: K8sService,
        store_service: StoreService,
        max_workers: int = 5
    ):
        """
        Initialize provisioning worker with thread pool.
        
        Args:
            helm_service: Helm service instance
            k8s_service: Kubernetes service instance
            store_service: Store service instance
            max_workers: Maximum number of concurrent provisioning tasks (default: 5)
        """
        self.helm_service = helm_service
        self.k8s_service = k8s_service
        self.store_service = store_service
        self.max_workers = max_workers
        
        # Thread pool executor for concurrent provisioning
        self.executor: Optional[ThreadPoolExecutor] = None
        
        # Track active futures to prevent duplicate submissions
        self.active_futures: Dict[str, Future] = {}
        
        self.running = False
        
        logger.info(f"ProvisioningWorker initialized with max_workers={max_workers}")
    
    def start(self):
        """
        Start the provisioning worker thread pool.
        
        This should be called once during backend initialization.
        """
        if self.running:
            logger.warning("ProvisioningWorker already running")
            return
        
        self.running = True
        self.executor = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="provision-worker"
        )
        logger.info(f"ProvisioningWorker started with {self.max_workers} worker threads")
    
    def stop(self):
        """Stop the provisioning worker and wait for active tasks."""
        if not self.running:
            return
        
        logger.info("Stopping ProvisioningWorker...")
        self.running = False
        
        if self.executor:
            logger.info("Shutting down thread pool (waiting for active tasks)...")
            self.executor.shutdown(wait=True, cancel_futures=False)
        
        logger.info("ProvisioningWorker stopped")
    
    def submit_provisioning_task(self, store_id: str):
        """
        Submit a store for provisioning to the thread pool.
        
        This is called by the API layer after creating a store record.
        The task is submitted to the thread pool and executed concurrently.
        
        Args:
            store_id: ID of the store to provision
        """
        # Prevent duplicate submissions
        if store_id in self.active_futures:
            future = self.active_futures[store_id]
            if not future.done():
                logger.warning(f"Store {store_id} already has an active provisioning task, skipping duplicate submission")
                return
            else:
                # Previous task completed, remove it
                del self.active_futures[store_id]
        
        logger.info(f"Submitting provisioning task for store: {store_id}")
        
        # Submit to thread pool
        future = self.executor.submit(self._provision_store, store_id)
        self.active_futures[store_id] = future
        
        # Add callback to clean up completed futures
        def cleanup_callback(f):
            if store_id in self.active_futures:
                del self.active_futures[store_id]
        
        future.add_done_callback(cleanup_callback)
    
    def resume_provisioning_stores(self):
        """
        Resume provisioning for stores in PROVISIONING state.
        
        This is called during backend initialization to handle crash recovery.
        Any stores that were being provisioned when the backend crashed/restarted
        will be resumed concurrently.
        """
        logger.info("Resuming provisioning for stores in PROVISIONING state")
        
        provisioning_stores = self.store_service.get_provisioning_stores()
        
        if not provisioning_stores:
            logger.info("No stores to resume")
            return
        
        logger.info(f"Resuming {len(provisioning_stores)} stores")
        
        for store in provisioning_stores:
            # Check if Helm release already exists
            helm_status = self.helm_service.get_release_status(
                store.helm_release,
                store.namespace
            )
            
            if helm_status:
                logger.info(f"Store {store.id} has existing Helm release (status: {helm_status}), resuming checks")
            else:
                logger.info(f"Store {store.id} has no Helm release, restarting provisioning")
            
            # Submit for concurrent provisioning/checking
            self.submit_provisioning_task(store.id)
    
    def _provision_store(self, store_id: str):
        """
        Provision a single store (executed in thread pool worker).
        
        This is the core reconciliation logic:
        1. Fetch store from DB
        2. Check if Helm release exists
        3. If not, install via Helm
        4. Poll Kubernetes for readiness
        5. Update DB with result
        
        This method is idempotent and can be safely retried.
        
        Args:
            store_id: Store ID to provision
        """
        logger.info(f"[{store_id}] Starting provisioning (thread pool)")
        
        # Fetch store from DB
        store = self.store_service.get_store_by_id(store_id)
        if not store:
            logger.error(f"[{store_id}] Store not found in database")
            return
        
        # Verify store is in correct state
        if store.status not in ['PROVISIONING']:
            logger.warning(f"[{store_id}] Not in PROVISIONING state (current: {store.status}), skipping")
            return
        
        try:
            # Step 1: Check if Helm release already exists (idempotency)
            helm_status = self.helm_service.get_release_status(
                store.helm_release,
                store.namespace
            )
            
            if not helm_status:
                # Step 2: Install Helm release
                logger.info(f"[{store_id}] Installing Helm release")
                
                helm_values = self.store_service.get_helm_values(store)
                success, output = self.helm_service.install(
                    release_name=store.helm_release,
                    namespace=store.namespace,
                    values=helm_values
                )
                
                if not success:
                    # Helm install failed
                    logger.error(f"[{store_id}] Helm install failed: {output}")
                    self.store_service.update_store_status(
                        store_id,
                        status='FAILED',
                        failure_reason=f"Helm install failed: {output}"
                    )
                    return
                
                logger.info(f"[{store_id}] Helm install succeeded")
                
                # Give Kubernetes time to schedule pods after Helm install
                logger.info(f"[{store_id}] Waiting for pods to be scheduled...")
                time.sleep(15)  # Wait 15 seconds for initial pod scheduling
            else:
                logger.info(f"[{store_id}] Helm release already exists (status: {helm_status})")
            
            # Step 3: Poll Kubernetes for readiness
            logger.info(f"[{store_id}] Starting readiness checks")
            
            start_time = time.time()
            
            while True:
                # Check timeout
                elapsed = time.time() - start_time
                if elapsed > Config.PROVISIONING_TIMEOUT_SECONDS:
                    timeout_msg = f"Provisioning timed out after {Config.PROVISIONING_TIMEOUT_SECONDS} seconds"
                    logger.error(f"[{store_id}] {timeout_msg}")
                    self.store_service.update_store_status(
                        store_id,
                        status='FAILED',
                        failure_reason=timeout_msg
                    )
                    return
                
                # Check readiness
                ready, store_url, failure_reason = self.k8s_service.check_store_ready(
                    store.namespace,
                    f"{store.helm_release}-ingress"
                )
                
                if ready:
                    # Success!
                    logger.info(f"[{store_id}] Store is ready: {store_url}")
                    self.store_service.update_store_status(
                        store_id,
                        status='READY',
                        store_url=store_url
                    )
                    return
                
                if failure_reason:
                    # Permanent failure detected
                    logger.error(f"[{store_id}] Store failed: {failure_reason}")
                    self.store_service.update_store_status(
                        store_id,
                        status='FAILED',
                        failure_reason=failure_reason
                    )
                    return
                
                # Not ready yet, wait and retry
                logger.debug(f"[{store_id}] Not ready yet (elapsed: {elapsed:.1f}s), polling again...")
                time.sleep(Config.PROVISIONING_POLL_INTERVAL_SECONDS)
        
        except Exception as e:
            # Unexpected error
            error_msg = f"Unexpected error during provisioning: {str(e)}"
            logger.error(f"[{store_id}] {error_msg}", exc_info=True)
            self.store_service.update_store_status(
                store_id,
                status='FAILED',
                failure_reason=error_msg
            )
