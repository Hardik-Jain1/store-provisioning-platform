"""
Provisioning Worker

Handles asynchronous provisioning of stores.
This worker runs in a background thread and reconciles desired state (DB) with reality (K8s).
"""

import logging
import time
import threading
from queue import Queue, Empty
from typing import Optional

from models.store import Store
from services.helm_service import HelmService
from services.k8s_service import K8sService
from services.store_service import StoreService
from config import PROVISIONING_TIMEOUT_SECONDS, PROVISIONING_POLL_INTERVAL_SECONDS

logger = logging.getLogger(__name__)


class ProvisioningWorker:
    """
    Background worker for asynchronous store provisioning.
    
    This worker:
    1. Receives provisioning tasks via a queue
    2. Invokes Helm to install releases
    3. Polls Kubernetes to check readiness
    4. Updates database with status
    5. Enforces timeouts
    
    The worker is crash-safe: if it dies, stores remain in PROVISIONING state
    and will be resumed on backend restart.
    """
    
    def __init__(
        self,
        helm_service: HelmService,
        k8s_service: K8sService,
        store_service: StoreService
    ):
        """
        Initialize provisioning worker.
        
        Args:
            helm_service: Helm service instance
            k8s_service: Kubernetes service instance
            store_service: Store service instance
        """
        self.helm_service = helm_service
        self.k8s_service = k8s_service
        self.store_service = store_service
        
        # Task queue for provisioning requests
        self.task_queue: Queue = Queue()
        
        # Worker thread
        self.worker_thread: Optional[threading.Thread] = None
        self.running = False
        
        logger.info("ProvisioningWorker initialized")
    
    def start(self):
        """
        Start the provisioning worker thread.
        
        This should be called once during backend initialization.
        """
        if self.running:
            logger.warning("ProvisioningWorker already running")
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info("ProvisioningWorker started")
    
    def stop(self):
        """Stop the provisioning worker."""
        if not self.running:
            return
        
        logger.info("Stopping ProvisioningWorker...")
        self.running = False
        
        if self.worker_thread:
            self.worker_thread.join(timeout=10)
        
        logger.info("ProvisioningWorker stopped")
    
    def submit_provisioning_task(self, store_id: str):
        """
        Submit a store for provisioning.
        
        This is called by the API layer after creating a store record.
        The actual provisioning happens asynchronously in the worker thread.
        
        Args:
            store_id: ID of the store to provision
        """
        logger.info(f"Submitting provisioning task for store: {store_id}")
        self.task_queue.put(store_id)
    
    def resume_provisioning_stores(self):
        """
        Resume provisioning for stores in PROVISIONING state.
        
        This is called during backend initialization to handle crash recovery.
        Any stores that were being provisioned when the backend crashed/restarted
        will be resumed.
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
                # Submit for readiness checking (skip Helm install)
                self.task_queue.put(store.id)
            else:
                logger.info(f"Store {store.id} has no Helm release, restarting provisioning")
                # Helm install was never completed, restart from scratch
                self.task_queue.put(store.id)
    
    def _worker_loop(self):
        """
        Main worker loop.
        
        Continuously processes provisioning tasks from the queue.
        """
        logger.info("ProvisioningWorker loop started")
        
        while self.running:
            try:
                # Get next task with timeout to allow checking self.running
                store_id = self.task_queue.get(timeout=1)
                
                logger.info(f"Processing provisioning task for store: {store_id}")
                
                # Process the provisioning task
                self._provision_store(store_id)
                
                self.task_queue.task_done()
                
            except Empty:
                # No tasks, continue loop
                continue
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
                # Continue processing other tasks
    
    def _provision_store(self, store_id: str):
        """
        Provision a single store.
        
        This is the core reconciliation logic:
        1. Fetch store from DB
        2. Check if Helm release exists
        3. If not, install via Helm
        4. Poll Kubernetes for readiness
        5. Update DB with result
        
        Args:
            store_id: Store ID to provision
        """
        logger.info(f"Starting provisioning for store: {store_id}")
        
        # Fetch store from DB
        store = self.store_service.get_store_by_id(store_id)
        if not store:
            logger.error(f"Store {store_id} not found in database")
            return
        
        # Verify store is in correct state
        if store.status not in ['PROVISIONING']:
            logger.warning(f"Store {store_id} is not in PROVISIONING state (current: {store.status}), skipping")
            return
        
        try:
            # Step 1: Check if Helm release already exists (idempotency)
            helm_status = self.helm_service.get_release_status(
                store.helm_release,
                store.namespace
            )
            
            if not helm_status:
                # Step 2: Install Helm release
                logger.info(f"Installing Helm release for store: {store_id}")
                
                helm_values = self.store_service.get_helm_values(store)
                success, output = self.helm_service.install(
                    release_name=store.helm_release,
                    namespace=store.namespace,
                    values=helm_values
                )
                
                if not success:
                    # Helm install failed
                    logger.error(f"Helm install failed for store {store_id}: {output}")
                    self.store_service.update_store_status(
                        store_id,
                        status='FAILED',
                        failure_reason=f"Helm install failed: {output}"
                    )
                    return
                
                logger.info(f"Helm install succeeded for store {store_id}")
            else:
                logger.info(f"Helm release already exists for store {store_id} (status: {helm_status})")
            
            # Step 3: Poll Kubernetes for readiness
            logger.info(f"Starting readiness checks for store: {store_id}")
            
            start_time = time.time()
            
            while True:
                # Check timeout
                elapsed = time.time() - start_time
                if elapsed > PROVISIONING_TIMEOUT_SECONDS:
                    timeout_msg = f"Provisioning timed out after {PROVISIONING_TIMEOUT_SECONDS} seconds"
                    logger.error(f"Store {store_id}: {timeout_msg}")
                    self.store_service.update_store_status(
                        store_id,
                        status='FAILED',
                        failure_reason=timeout_msg
                    )
                    return
                
                # Check readiness
                ready, store_url, failure_reason = self.k8s_service.check_store_ready(
                    store.namespace
                )
                
                if ready:
                    # Success!
                    logger.info(f"Store {store_id} is ready: {store_url}")
                    self.store_service.update_store_status(
                        store_id,
                        status='READY',
                        store_url=store_url
                    )
                    return
                
                if failure_reason:
                    # Permanent failure detected
                    logger.error(f"Store {store_id} failed: {failure_reason}")
                    self.store_service.update_store_status(
                        store_id,
                        status='FAILED',
                        failure_reason=failure_reason
                    )
                    return
                
                # Not ready yet, wait and retry
                logger.debug(f"Store {store_id} not ready yet (elapsed: {elapsed:.1f}s), polling again...")
                time.sleep(PROVISIONING_POLL_INTERVAL_SECONDS)
        
        except Exception as e:
            # Unexpected error
            error_msg = f"Unexpected error during provisioning: {str(e)}"
            logger.error(f"Store {store_id}: {error_msg}", exc_info=True)
            self.store_service.update_store_status(
                store_id,
                status='FAILED',
                failure_reason=error_msg
            )
