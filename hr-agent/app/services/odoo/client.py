"""Odoo XML-RPC Client Wrapper for Odoo 17+."""

import logging
import xmlrpc.client
from typing import Any, Dict, List, Optional, Set

from app.config import settings
from app.core.exceptions import OdooAuthenticationError, OdooConnectionError, OdooModuleNotFoundError

logger = logging.getLogger(__name__)


class OdooClient:
    """
    Singleton Odoo XML-RPC client for connecting to Odoo 17+.
    Handles authentication and provides execute_kw wrapper.
    Includes module availability checking for graceful degradation.
    """

    _instance: Optional["OdooClient"] = None

    def __new__(cls) -> "OdooClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.url = settings.ODOO_URL.rstrip("/")
        self.db = settings.ODOO_DB
        self.username = settings.ODOO_USER
        self.password = settings.ODOO_PASSWORD
        self._uid: Optional[int] = None
        self._common: Optional[xmlrpc.client.ServerProxy] = None
        self._models: Optional[xmlrpc.client.ServerProxy] = None
        self._available_models: Set[str] = set()
        self._initialized = True

    def connect(self) -> int:
        """
        Authenticate with Odoo and get user ID.

        Returns:
            User ID from Odoo

        Raises:
            OdooConnectionError: If unable to connect to Odoo
            OdooAuthenticationError: If authentication fails
        """
        try:
            self._common = xmlrpc.client.ServerProxy(
                f"{self.url}/xmlrpc/2/common",
                allow_none=True,
            )

            # Test connection by getting version
            version = self._common.version()
            logger.info(f"Connected to Odoo {version.get('server_version', 'unknown')}")

        except Exception as e:
            logger.error(f"Failed to connect to Odoo at {self.url}: {e}")
            raise OdooConnectionError(
                f"Unable to connect to Odoo at {self.url}",
                details={"error": str(e)},
            )

        try:
            self._uid = self._common.authenticate(
                self.db,
                self.username,
                self.password,
                {},
            )

            if not self._uid:
                raise OdooAuthenticationError(
                    "Odoo authentication failed - invalid credentials",
                    details={"db": self.db, "user": self.username},
                )

            self._models = xmlrpc.client.ServerProxy(
                f"{self.url}/xmlrpc/2/object",
                allow_none=True,
            )

            logger.info(f"Authenticated as user {self.username} (uid: {self._uid})")

            # Check available modules
            self._check_available_modules()

            return self._uid

        except OdooAuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Odoo authentication error: {e}")
            raise OdooAuthenticationError(
                "Odoo authentication failed",
                details={"error": str(e)},
            )

    def _check_available_modules(self) -> None:
        """Check which HR modules are available in Odoo."""
        models_to_check = [
            "hr.employee",
            "hr.department",
            "hr.job",
            "hr.applicant",
            "hr.recruitment.stage",
            "hr.appraisal",
            "hr.appraisal.goal",
            "hr.attendance",
            "hr.leave",
            "hr.leave.type",
            "hr.contract",
            "calendar.event",
        ]

        for model in models_to_check:
            try:
                # Try to get model info
                self.execute_kw("ir.model", "search", [[("model", "=", model)]], {"limit": 1})
                result = self.execute_kw("ir.model", "search_count", [[("model", "=", model)]])
                if result > 0:
                    self._available_models.add(model)
                    logger.debug(f"Model {model} is available")
            except Exception:
                logger.debug(f"Model {model} is not available")

        logger.info(f"Available Odoo models: {self._available_models}")

    def is_model_available(self, model: str) -> bool:
        """Check if a specific Odoo model is available."""
        self.ensure_connected()
        return model in self._available_models

    def require_model(self, model: str) -> None:
        """
        Ensure a model is available, raise error if not.

        Raises:
            OdooModuleNotFoundError: If the model is not available
        """
        if not self.is_model_available(model):
            raise OdooModuleNotFoundError(
                f"Required Odoo model '{model}' is not available. "
                f"Please install the corresponding module.",
                details={"model": model},
            )

    def ensure_connected(self) -> None:
        """Ensure client is connected, reconnect if necessary."""
        if not self._uid or not self._models:
            self.connect()

    def execute_kw(
        self,
        model: str,
        method: str,
        args: List[Any],
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Execute Odoo model method via XML-RPC.

        Args:
            model: Odoo model name (e.g., 'hr.employee')
            method: Method to call (e.g., 'search_read')
            args: Positional arguments for the method
            kwargs: Keyword arguments for the method

        Returns:
            Result from Odoo

        Raises:
            OdooConnectionError: If not connected or call fails
        """
        self.ensure_connected()

        try:
            return self._models.execute_kw(
                self.db,
                self._uid,
                self.password,
                model,
                method,
                args,
                kwargs or {},
            )
        except Exception as e:
            logger.error(f"Odoo execute_kw error on {model}.{method}: {e}")
            raise OdooConnectionError(
                f"Odoo operation failed: {model}.{method}",
                details={"error": str(e), "model": model, "method": method},
            )

    def search(
        self,
        model: str,
        domain: List,
        limit: Optional[int] = None,
        offset: int = 0,
        order: Optional[str] = None,
    ) -> List[int]:
        """
        Search for record IDs matching domain.

        Args:
            model: Odoo model name
            domain: Search domain (e.g., [('active', '=', True)])
            limit: Maximum records to return
            offset: Number of records to skip
            order: Sort order (e.g., 'create_date desc')

        Returns:
            List of record IDs
        """
        kwargs = {"offset": offset}
        if limit:
            kwargs["limit"] = limit
        if order:
            kwargs["order"] = order

        return self.execute_kw(model, "search", [domain], kwargs)

    def read(
        self,
        model: str,
        ids: List[int],
        fields: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Read records by IDs.

        Args:
            model: Odoo model name
            ids: List of record IDs to read
            fields: Fields to read (None for all)

        Returns:
            List of record dictionaries
        """
        kwargs = {}
        if fields:
            kwargs["fields"] = fields

        return self.execute_kw(model, "read", [ids], kwargs)

    def search_read(
        self,
        model: str,
        domain: List,
        fields: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        order: Optional[str] = None,
    ) -> List[Dict]:
        """
        Search and read records in one call.

        Args:
            model: Odoo model name
            domain: Search domain
            fields: Fields to read
            limit: Maximum records
            offset: Records to skip
            order: Sort order

        Returns:
            List of record dictionaries
        """
        kwargs = {"offset": offset}
        if fields:
            kwargs["fields"] = fields
        if limit:
            kwargs["limit"] = limit
        if order:
            kwargs["order"] = order

        return self.execute_kw(model, "search_read", [domain], kwargs)

    def search_count(self, model: str, domain: List) -> int:
        """
        Count records matching domain.

        Args:
            model: Odoo model name
            domain: Search domain

        Returns:
            Number of matching records
        """
        return self.execute_kw(model, "search_count", [domain])

    def create(self, model: str, values: Dict) -> int:
        """
        Create a new record.

        Args:
            model: Odoo model name
            values: Field values for new record

        Returns:
            ID of created record
        """
        return self.execute_kw(model, "create", [values])

    def write(self, model: str, ids: List[int], values: Dict) -> bool:
        """
        Update existing records.

        Args:
            model: Odoo model name
            ids: Record IDs to update
            values: Field values to update

        Returns:
            True if successful
        """
        return self.execute_kw(model, "write", [ids, values])

    def unlink(self, model: str, ids: List[int]) -> bool:
        """
        Delete records.

        Args:
            model: Odoo model name
            ids: Record IDs to delete

        Returns:
            True if successful
        """
        return self.execute_kw(model, "unlink", [ids])

    def check_connection(self) -> Dict[str, Any]:
        """
        Check Odoo connection status.

        Returns:
            Connection status with version info
        """
        try:
            self.ensure_connected()
            version = self._common.version()
            return {
                "connected": True,
                "server_version": version.get("server_version"),
                "server_serie": version.get("server_serie"),
                "protocol_version": version.get("protocol_version"),
                "uid": self._uid,
                "database": self.db,
                "available_models": list(self._available_models),
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
            }

    def get_available_modules_status(self) -> Dict[str, bool]:
        """Get status of HR-related modules."""
        return {
            "hr_base": self.is_model_available("hr.employee"),
            "hr_recruitment": self.is_model_available("hr.applicant"),
            "hr_appraisal": self.is_model_available("hr.appraisal"),
            "hr_attendance": self.is_model_available("hr.attendance"),
            "hr_holidays": self.is_model_available("hr.leave"),
            "hr_contract": self.is_model_available("hr.contract"),
            "calendar": self.is_model_available("calendar.event"),
        }


def get_odoo_client() -> OdooClient:
    """Get the singleton Odoo client instance."""
    return OdooClient()
