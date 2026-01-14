"""
Firebase Client for mega-agent2.

Async wrapper around Firebase Admin SDK and Firestore client.
Supports Firestore operations and project management.
"""

import os
import json
import asyncio
from typing import Any, Dict, List, Optional

try:
    import firebase_admin
    from firebase_admin import credentials, firestore as admin_firestore, initialize_app, get_app, delete_app
    FIREBASE_ADMIN_AVAILABLE = True
except ImportError:
    FIREBASE_ADMIN_AVAILABLE = False

try:
    from google.cloud import firestore as cloud_firestore
    from google.oauth2 import service_account
    FIRESTORE_CLIENT_AVAILABLE = True
except ImportError:
    FIRESTORE_CLIENT_AVAILABLE = False


class FirebaseClient:
    """Async client for Firebase services."""

    def __init__(self, credential_file: str = 'google-credentials-aquarius.json',
                 project_id: Optional[str] = None):
        """
        Initialize Firebase client.

        Args:
            credential_file: Path to service account credentials
            project_id: Optional project ID (defaults to project_id in credentials)
        """
        if not credential_file.startswith('/'):
            # Make it relative to working directory if not absolute
            credential_file = os.path.abspath(credential_file)

        self.credential_file = credential_file

        # Load project info
        with open(credential_file, 'r') as f:
            cred_data = json.load(f)
            self.project_id = project_id or cred_data.get('project_id')

        # Initialize Firebase Admin SDK
        self._app = None
        if FIREBASE_ADMIN_AVAILABLE:
            try:
                # Try to get existing app or create new one
                try:
                    self._app = get_app()
                except ValueError:
                    # No app exists, create one
                    cred = credentials.Certificate(credential_file)
                    self._app = initialize_app(cred, {
                        'projectId': self.project_id
                    })
            except Exception as e:
                # Non-critical, we can still use Firestore client
                pass

        # Initialize Firestore client
        self._db = None
        if FIRESTORE_CLIENT_AVAILABLE:
            try:
                creds = service_account.Credentials.from_service_account_file(
                    credential_file,
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
                self._db = cloud_firestore.Client(
                    project=self.project_id,
                    credentials=creds
                )
            except Exception as e:
                raise Exception(f"Could not initialize Firestore client: {e}")

    def _get_firestore(self):
        """Get Firestore database instance (synchronous)."""
        if not self._db:
            raise Exception("Firestore client not available")
        return self._db

    # ============================================================================
    # Firestore - Document Operations
    # ============================================================================

    async def read_document(self, collection: str, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Read a document from Firestore.

        Args:
            collection: Collection name
            document_id: Document ID

        Returns:
            Document data or None if not exists
        """
        def _read():
            db = self._get_firestore()
            doc_ref = db.collection(collection).document(document_id)
            doc = doc_ref.get()

            if doc.exists:
                return doc.to_dict()
            return None

        return await asyncio.to_thread(_read)

    async def write_document(self, collection: str, document_id: str, data: Dict[str, Any]) -> bool:
        """
        Write a document to Firestore.

        Args:
            collection: Collection name
            document_id: Document ID
            data: Document data

        Returns:
            True if successful
        """
        def _write():
            db = self._get_firestore()
            doc_ref = db.collection(collection).document(document_id)
            doc_ref.set(data)
            return True

        return await asyncio.to_thread(_write)

    async def update_document(self, collection: str, document_id: str, data: Dict[str, Any]) -> bool:
        """
        Update a document in Firestore.

        Args:
            collection: Collection name
            document_id: Document ID
            data: Fields to update

        Returns:
            True if successful
        """
        def _update():
            db = self._get_firestore()
            doc_ref = db.collection(collection).document(document_id)
            doc_ref.update(data)
            return True

        return await asyncio.to_thread(_update)

    async def delete_document(self, collection: str, document_id: str) -> bool:
        """
        Delete a document from Firestore.

        Args:
            collection: Collection name
            document_id: Document ID

        Returns:
            True if successful
        """
        def _delete():
            db = self._get_firestore()
            doc_ref = db.collection(collection).document(document_id)
            doc_ref.delete()
            return True

        return await asyncio.to_thread(_delete)

    # ============================================================================
    # Firestore - Collection Operations
    # ============================================================================

    async def query_collection(
        self,
        collection: str,
        filters: Optional[List[tuple]] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query a Firestore collection.

        Args:
            collection: Collection name
            filters: List of (field, operator, value) tuples
            limit: Maximum number of results
            order_by: Field to order by

        Returns:
            List of documents
        """
        def _query():
            db = self._get_firestore()
            query = db.collection(collection)

            # Apply filters
            if filters:
                for field, operator, value in filters:
                    query = query.where(field, operator, value)

            # Apply ordering
            if order_by:
                query = query.order_by(order_by)

            # Apply limit
            if limit:
                query = query.limit(limit)

            # Execute query
            docs = query.stream()
            return [doc.to_dict() for doc in docs]

        return await asyncio.to_thread(_query)

    async def list_collections(self) -> List[str]:
        """List all collections in Firestore.

        Returns:
            List of collection IDs
        """
        def _list():
            db = self._get_firestore()
            collections = db.collections()
            return [col.id for col in collections]

        return await asyncio.to_thread(_list)

    async def get_all_documents(self, collection: str) -> List[Dict[str, Any]]:
        """Get all documents from a collection.

        Args:
            collection: Collection name

        Returns:
            List of all documents
        """
        return await self.query_collection(collection)

    # ============================================================================
    # Batch Operations
    # ============================================================================

    async def batch_write(self, operations: List[Dict[str, Any]]) -> bool:
        """
        Perform batch write operations.

        Args:
            operations: List of operation dicts with keys:
                - operation: 'set', 'update', or 'delete'
                - collection: Collection name
                - document_id: Document ID
                - data: Data to write (for set/update)

        Returns:
            True if successful
        """
        def _batch():
            db = self._get_firestore()
            batch = db.batch()

            for op in operations:
                doc_ref = db.collection(op['collection']).document(op['document_id'])

                if op['operation'] == 'set':
                    batch.set(doc_ref, op['data'])
                elif op['operation'] == 'update':
                    batch.update(doc_ref, op['data'])
                elif op['operation'] == 'delete':
                    batch.delete(doc_ref)

            batch.commit()
            return True

        return await asyncio.to_thread(_batch)

    # ============================================================================
    # Project Information
    # ============================================================================

    async def get_project_info(self) -> Dict[str, Any]:
        """Get Firebase project information.

        Returns:
            Project info dict
        """
        def _get_info():
            try:
                # Try to get project info using Firebase Management API
                from google_cloud_api import GoogleCloudAPI

                api = GoogleCloudAPI(credential_file=self.credential_file)
                project = api.firebase.projects().get(name=f'projects/{self.project_id}').execute()

                return {
                    "project_id": self.project_id,
                    "display_name": project.get("displayName"),
                    "project_number": project.get("projectNumber"),
                    "state": project.get("state"),
                    "status": "active"
                }
            except Exception:
                # Project might not be initialized as Firebase project yet
                return {
                    "project_id": self.project_id,
                    "status": "not_initialized",
                    "message": "Project needs to be initialized in Firebase Console"
                }

        return await asyncio.to_thread(_get_info)

    def __del__(self):
        """Cleanup Firebase app on deletion."""
        if self._app and FIREBASE_ADMIN_AVAILABLE:
            try:
                delete_app(self._app)
            except:
                pass
