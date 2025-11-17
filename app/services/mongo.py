from __future__ import annotations

import os
from typing import Optional

import certifi
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

_CLIENT: Optional[MongoClient] = None


def _env_flag(name: str, *, default: bool = False) -> bool:
    """Return True if an env variable is set to a truthy value."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _uri_requires_tls(uri: str) -> bool:
    lowered = uri.lower()
    return uri.startswith("mongodb+srv://") or "tls=true" in lowered or "ssl=true" in lowered


def get_mongo_client() -> MongoClient:
    """Return a cached MongoClient bound to the configured URI."""
    global _CLIENT
    if _CLIENT is None:
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        timeout_ms = int(os.getenv("MONGODB_SELECTION_TIMEOUT_MS", "5000"))
        client_kwargs = {"serverSelectionTimeoutMS": timeout_ms}

        ca_file = os.getenv("MONGODB_TLS_CA_FILE")
        if ca_file:
            client_kwargs["tlsCAFile"] = ca_file
        elif _uri_requires_tls(uri):
            client_kwargs["tlsCAFile"] = certifi.where()

        if _env_flag("MONGODB_TLS_ALLOW_INVALID_CERTS"):
            client_kwargs["tlsAllowInvalidCertificates"] = True

        _CLIENT = MongoClient(uri, **client_kwargs)
    return _CLIENT


def get_database(db_name: Optional[str] = None) -> Database:
    """Return the target database, defaulting to the CIVICBRIEFS DB."""
    name = db_name or os.getenv("MONGODB_DB", "civicbriefs")
    return get_mongo_client()[name]


def get_collection(name: str, db_name: Optional[str] = None) -> Collection:
    """Access a collection on the configured database."""
    return get_database(db_name)[name]
