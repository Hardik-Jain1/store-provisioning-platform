"""
Store API Routes using Flask-RESTful

REST API endpoints for store management.
All routes return immediately; provisioning happens asynchronously.
"""

import logging
from flask import request
from flask_restful import Resource, Api, abort, fields, marshal_with

from services.store_service import StoreService
from services.helm_service import HelmService

logger = logging.getLogger(__name__)

# Service instances (injected by app initialization)
_store_service: StoreService = None
_helm_service: HelmService = None
_provisioning_worker = None


def init_stores_api(store_service: StoreService, helm_service: HelmService, provisioning_worker):
    """
    Initialize the stores API with service dependencies.
    
    This must be called during app initialization.
    """
    global _store_service, _helm_service, _provisioning_worker
    _store_service = store_service
    _helm_service = helm_service
    _provisioning_worker = provisioning_worker
    logger.info("Store API initialized with Flask-RESTful")


# Define output fields for marshalling
store_fields = {
    'id': fields.String,
    'name': fields.String,
    'engine': fields.String,
    'namespace': fields.String,
    'status': fields.String,
    'store_url': fields.String,
    'failure_reason': fields.String,
    'created_at': fields.DateTime(dt_format='iso8601'),
    'updated_at': fields.DateTime(dt_format='iso8601'),
}


class StoreListResource(Resource):
    """
    Resource for listing all stores and creating new stores.
    
    GET /stores - List all stores
    POST /stores - Create a new store
    """
    
    def get(self):
        """
        List all stores.
        
        Returns:
            200: List of stores
            500: Internal server error
        """
        try:
            stores = _store_service.list_stores()
            
            stores_data = []
            for store in stores:
                stores_data.append({
                    'id': store.id,
                    'name': store.name,
                    'engine': store.engine,
                    'namespace': store.namespace,
                    'status': store.status,
                    'store_url': store.store_url,
                    'failure_reason': store.failure_reason,
                    'admin_username': store.admin_username,
                    'admin_email': store.admin_email,
                    'created_at': store.created_at.isoformat() if store.created_at else None,
                    'updated_at': store.updated_at.isoformat() if store.updated_at else None,
                })
            
            return {'stores': stores_data}, 200
            
        except Exception as e:
            logger.error(f"Failed to list stores: {e}", exc_info=True)
            return {'message': 'Internal server error'}, 500
    
    def post(self):
        """
        Create a new store.
        
        Request body:
        {
            "name": "my-store",
            "engine": "woocommerce",
            "admin_username": "admin",
            "admin_password": "MySecureAdminPass789!",
            "admin_email": "admin@example.com"
        }
        
        Returns:
            202: Store creation request accepted (PROVISIONING)
            400: Validation error
            500: Internal server error
        """
        try:
            data = request.get_json()
            
            # Validate request
            if not data:
                return {'message': 'Request body is required'}, 400
            
            name = data.get('name')
            engine = data.get('engine')
            admin_username = data.get('admin_username')
            admin_password = data.get('admin_password')
            admin_email = data.get('admin_email')
            
            if not name:
                return {'message': 'Field "name" is required'}, 400
            
            if not engine:
                return {'message': 'Field "engine" is required'}, 400
            
            if not admin_username:
                return {'message': 'Field "admin_username" is required'}, 400
            
            if not admin_password:
                return {'message': 'Field "admin_password" is required'}, 400
            
            if not admin_email:
                return {'message': 'Field "admin_email" is required'}, 400
            
            # Create store record (this is synchronous and fast)
            store = _store_service.create_store(
                name=name,
                engine=engine,
                admin_username=admin_username,
                admin_password=admin_password,
                admin_email=admin_email
            )
            
            # Submit for async provisioning
            _provisioning_worker.submit_provisioning_task(store.id)
            
            logger.info(f"Store creation request accepted: {store.id}")
            
            # Return immediately with PROVISIONING status
            return {
                'id': store.id,
                'name': store.name,
                'engine': store.engine,
                'namespace': store.namespace,
                'status': store.status,
                'admin_username': store.admin_username,
                'admin_email': store.admin_email,
                'created_at': store.created_at.isoformat()
            }, 202  # 202 Accepted
            
        except ValueError as e:
            # Validation error from service layer
            logger.warning(f"Store creation validation error: {e}")
            return {'message': str(e)}, 400
        
        except Exception as e:
            # Unexpected error
            logger.error(f"Store creation failed: {e}", exc_info=True)
            return {'message': 'Internal server error'}, 500


class StoreResource(Resource):
    """
    Resource for individual store operations.
    
    GET /stores/<store_id> - Get store details
    DELETE /stores/<store_id> - Delete a store
    """
    
    def get(self, store_id: str):
        """
        Get a single store by ID.
        
        Args:
            store_id: Store identifier
            
        Returns:
            200: Store details
            404: Store not found
            500: Internal server error
        """
        try:
            store = _store_service.get_store_by_id(store_id)
            
            if not store:
                return {'message': 'Store not found'}, 404
            
            return {
                'id': store.id,
                'name': store.name,
                'engine': store.engine,
                'namespace': store.namespace,
                'helm_release': store.helm_release,
                'status': store.status,
                'store_url': store.store_url,
                'failure_reason': store.failure_reason,
                'admin_username': store.admin_username,
                'admin_email': store.admin_email,
                'created_at': store.created_at.isoformat() if store.created_at else None,
                'updated_at': store.updated_at.isoformat() if store.updated_at else None,
            }, 200
            
        except Exception as e:
            logger.error(f"Failed to get store {store_id}: {e}", exc_info=True)
            return {'message': 'Internal server error'}, 500
    
    def delete(self, store_id: str):
        """
        Delete a store.
        
        Args:
            store_id: Store identifier
            
        Returns:
            200: Store deleted successfully
            400: Invalid state for deletion
            404: Store not found
            500: Deletion failed
        """
        try:
            store = _store_service.get_store_by_id(store_id)
            
            if not store:
                return {'message': 'Store not found'}, 404
            
            # Prevent deletion of already deleted stores
            if store.status == 'DELETED':
                return {'message': 'Store already deleted'}, 400
            
            # Mark as DELETING
            _store_service.mark_store_deleting(store_id)
            
            logger.info(f"Deleting store: {store_id}")
            
            # Uninstall Helm release (this is relatively fast, so we do it synchronously)
            success, output = _helm_service.uninstall(
                release_name=store.helm_release,
                namespace=store.namespace
            )
            
            if success:
                # Mark as DELETED
                _store_service.mark_store_deleted(store_id)
                logger.info(f"Store deleted successfully: {store_id}")
                
                return {
                    'id': store_id,
                    'status': 'DELETED',
                    'message': 'Store deleted successfully'
                }, 200
            else:
                # Helm uninstall failed
                logger.error(f"Helm uninstall failed for store {store_id}: {output}")
                
                # Mark as FAILED
                _store_service.update_store_status(
                    store_id,
                    status='FAILED',
                    failure_reason=f"Delete failed: {output}"
                )
                
                return {
                    'message': 'Failed to delete store',
                    'details': output
                }, 500
        
        except Exception as e:
            logger.error(f"Store deletion failed: {e}", exc_info=True)
            return {
                    'message': 'Failed to delete store',
                    'details': output
                }, 500


class HealthResource(Resource):
    """
    Health check endpoint.
    
    GET /health - Check API health
    """
    
    def get(self):
        """
        Health check endpoint.
        
        Returns:
            200: Service is healthy
        """
        return {
            'status': 'healthy',
            'service': 'store-provisioning-backend'
        }, 200


def register_resources(api: Api):
    """
    Register all REST resources with the API.
    
    Args:
        api: Flask-RESTful Api instance
    """
    api.add_resource(HealthResource, '/health')
    api.add_resource(StoreListResource, '/stores')
    api.add_resource(StoreResource, '/stores/<string:store_id>')
    
    logger.info("REST resources registered")