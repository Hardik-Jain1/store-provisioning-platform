"""
Store Model

Represents the source of truth for store lifecycle state.
The database is authoritative for idempotency and crash recovery.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Store(Base):
    """
    Store model representing ecommerce store instances.
    
    State transitions:
    - Create store → PROVISIONING
    - Provision success → READY
    - Provision failure → FAILED
    - Delete store → DELETING → DELETED
    """
    __tablename__ = 'stores'
    
    # Primary identifier (deterministic for idempotency)
    id = Column(String, primary_key=True, nullable=False)
    
    # User-friendly name (must be unique)
    name = Column(String, unique=True, nullable=False, index=True)
    
    # Engine type: 'woocommerce' or 'medusa'
    engine = Column(String, nullable=False)
    
    # Kubernetes namespace (deterministic: store-{id})
    namespace = Column(String, nullable=False)
    
    # Helm release name (deterministic: equals id)
    helm_release = Column(String, nullable=False)
    
    # Current lifecycle state
    # Valid values: PROVISIONING, READY, FAILED, DELETING, DELETED
    status = Column(String, nullable=False)
    
    # Failure reason (populated only when status = FAILED)
    failure_reason = Column(Text, nullable=True)
    
    # Store URL (populated when status = READY)
    store_url = Column(String, nullable=True)
    
    # Database credentials
    db_root_password = Column(String, nullable=False)
    db_name = Column(String, nullable=False)
    db_username = Column(String, nullable=False)
    db_password = Column(String, nullable=False)
    
    # Admin credentials
    admin_username = Column(String, nullable=False)
    admin_password = Column(String, nullable=False)
    admin_email = Column(String, nullable=False)
    
    # Timestamps for audit trail
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<Store(id={self.id}, name={self.name}, engine={self.engine}, status={self.status})>"
    
    def to_dict(self):
        """Convert store to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'engine': self.engine,
            'namespace': self.namespace,
            'helm_release': self.helm_release,
            'status': self.status,
            'failure_reason': self.failure_reason,
            'store_url': self.store_url,
            'admin_username': self.admin_username,
            'admin_email': self.admin_email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
