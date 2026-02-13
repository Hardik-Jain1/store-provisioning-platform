"""
Store Service

Business logic layer for store operations.
This service orchestrates between the database, Helm, and Kubernetes.
"""

import logging
import uuid
import secrets
import string
from datetime import datetime, timezone
from typing import List, Optional, Dict

from models.store import Store
from db.session import get_db_session, session_scope
from config import Config

logger = logging.getLogger(__name__)


class StoreService:
    """
    Service for managing store lifecycle.
    
    Responsibilities:
    - Create store records (source of truth)
    - Validate store creation requests
    - Query store state
    - Coordinate store deletion
    - Enforce idempotency
    """
    
    def __init__(self):
        """Initialize store service."""
        logger.info("StoreService initialized")
    
    def _generate_secure_password(self, length: int = 16) -> str:
        """
        Generate a secure random password.
        
        Args:
            length: Password length (default: 16)
        
        Returns:
            Secure random password
        """
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    def create_store(self, name: str, engine: str, admin_username: str, admin_password: str, admin_email: str) -> Store:
        """
        Create a new store record in the database.
        
        This is the FIRST step in provisioning. The store record is created
        BEFORE any Helm/Kubernetes interaction to ensure idempotency.
        
        Args:
            name: User-friendly store name (must be unique)
            engine: Engine type ('woocommerce' or 'medusa')
            admin_username: Admin username for the store
            admin_password: Admin password for the store
            admin_email: Admin email for the store
        
        Returns:
            Created Store object
        
        Raises:
            ValueError: If validation fails
        """
        logger.info(f"Creating store: name={name}, engine={engine}, admin_username={admin_username}, admin_email={admin_email}")
        
        # Validate engine
        valid_engines = ['woocommerce', 'medusa']
        if engine not in valid_engines:
            raise ValueError(f"Invalid engine '{engine}'. Must be one of: {valid_engines}")
        
        # Validate name
        if not name or not name.strip():
            raise ValueError("Store name cannot be empty")
        
        name = name.strip()
        
        # Validate admin fields
        if not admin_username or not admin_username.strip():
            raise ValueError("Admin username cannot be empty")
        if not admin_password or not admin_password.strip():
            raise ValueError("Admin password cannot be empty")
        if not admin_email or not admin_email.strip():
            raise ValueError("Admin email cannot be empty")
        
        admin_username = admin_username.strip()
        admin_password = admin_password.strip()
        admin_email = admin_email.strip()
        
        # Check for name uniqueness
        session = get_db_session()
        try:
            existing = session.query(Store).filter_by(name=name).first()
            if existing:
                raise ValueError(f"Store with name '{name}' already exists")
            
            # Generate deterministic identifiers
            # In production, you might want a more sophisticated ID generation
            store_id = f"{name}-{uuid.uuid4().hex[:8]}"
            namespace = f"store-{store_id}"
            helm_release = store_id  # Release name = store ID for determinism
            
            # Generate store domain
            store_domain = f"{name}.{Config.BASE_DOMAIN}"
            
            # Generate database credentials
            db_root_password = self._generate_secure_password(20)
            db_password = self._generate_secure_password(20)
            db_name = f"store_{name.replace('-', '_')}_db"
            db_username = f"user_{name.replace('-', '_')}"
            
            # Create store record
            store = Store(
                id=store_id,
                name=name,
                engine=engine,
                namespace=namespace,
                helm_release=helm_release,
                status='PROVISIONING',
                failure_reason=None,
                store_url=None,
                db_root_password=db_root_password,
                db_name=db_name,
                db_username=db_username,
                db_password=db_password,
                admin_username=admin_username,
                admin_password=admin_password,
                admin_email=admin_email,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            session.add(store)
            session.commit()
            session.refresh(store)
            
            logger.info(f"Store created: {store}")
            return store
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create store: {e}")
            raise
        finally:
            session.close()
    
    def get_store_by_id(self, store_id: str) -> Optional[Store]:
        """
        Get a store by ID.
        
        Args:
            store_id: Store ID
        
        Returns:
            Store object or None if not found
        """
        session = get_db_session()
        try:
            store = session.query(Store).filter_by(id=store_id).first()
            if store:
                # Detach from session so it can be used outside
                session.expunge(store)
            return store
        finally:
            session.close()
    
    def get_store_by_name(self, name: str) -> Optional[Store]:
        """
        Get a store by name.
        
        Args:
            name: Store name
        
        Returns:
            Store object or None if not found
        """
        session = get_db_session()
        try:
            store = session.query(Store).filter_by(name=name).first()
            if store:
                session.expunge(store)
            return store
        finally:
            session.close()
    
    def list_stores(self) -> List[Store]:
        """
        List all stores.
        
        Returns:
            List of Store objects (empty list if no stores exist)
        """
        session = get_db_session()
        try:
            stores = session.query(Store).order_by(Store.created_at.desc()).all()
            # Detach all stores from session
            for store in stores:
                session.expunge(store)
            return stores
        finally:
            session.close()
    
    def update_store_status(
        self,
        store_id: str,
        status: str,
        failure_reason: Optional[str] = None,
        store_url: Optional[str] = None
    ) -> bool:
        """
        Update store status.
        
        This is called by the provisioning worker as it reconciles state.
        
        Args:
            store_id: Store ID
            status: New status
            failure_reason: Failure reason (if status is FAILED)
            store_url: Store URL (if status is READY)
        
        Returns:
            True if update succeeded, False otherwise
        """
        session = get_db_session()
        try:
            store = session.query(Store).filter_by(id=store_id).first()
            if not store:
                logger.error(f"Store {store_id} not found for status update")
                return False
            
            logger.info(f"Updating store {store_id} status: {store.status} -> {status}")
            
            store.status = status
            store.updated_at = datetime.now(timezone.utc)
            
            if failure_reason:
                store.failure_reason = failure_reason
            
            if store_url:
                store.store_url = store_url
            
            session.commit()
            logger.info(f"Store {store_id} status updated successfully")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update store status: {e}")
            return False
        finally:
            session.close()
    
    def mark_store_deleting(self, store_id: str) -> bool:
        """
        Mark a store as DELETING.
        
        This is the first step in the deletion flow.
        
        Args:
            store_id: Store ID
        
        Returns:
            True if successful, False otherwise
        """
        return self.update_store_status(store_id, 'DELETING')
    
    def mark_store_deleted(self, store_id: str) -> bool:
        """
        Mark a store as DELETED.
        
        This is the final step after Helm uninstall succeeds.
        
        Args:
            store_id: Store ID
        
        Returns:
            True if successful, False otherwise
        """
        return self.update_store_status(store_id, 'DELETED')
    
    def get_provisioning_stores(self) -> List[Store]:
        """
        Get all stores in PROVISIONING state.
        
        This is used for crash recovery: when the backend restarts,
        it resumes provisioning for any stores that were in progress.
        
        Returns:
            List of stores in PROVISIONING state
        """
        session = get_db_session()
        try:
            stores = session.query(Store).filter_by(status='PROVISIONING').all()
            # Detach from session
            for store in stores:
                session.expunge(store)
            logger.info(f"Found {len(stores)} stores in PROVISIONING state")
            return stores
        finally:
            session.close()
    
    def get_helm_values(self, store: Store) -> Dict[str, str]:
        """
        Generate Helm values for a store.
        
        These values are passed to Helm via --set flags.
        The Helm chart uses these to customize the deployment.
        
        Args:
            store: Store object
        
        Returns:
            Dictionary of Helm values
        """
        # Generate domain
        domain = f"{store.name}.{Config.BASE_DOMAIN}"
        
        values = {
            'store.id': store.id,
            'store.name': store.name,
            'store.namespace': store.namespace,
            'store.engine': store.engine,
            'store.domain': domain,
            'secrets.database.rootPassword': store.db_root_password,
            'secrets.database.name': store.db_name,
            'secrets.database.username': store.db_username,
            'secrets.database.password': store.db_password,
            'secrets.admin.username': store.admin_username,
            'secrets.admin.password': store.admin_password,
            'secrets.admin.email': store.admin_email,
        }
        
        logger.debug(f"Generated Helm values for store {store.id}: {values}")
        return values
