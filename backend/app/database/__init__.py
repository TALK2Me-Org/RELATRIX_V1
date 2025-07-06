"""
Database package for RELATRIX backend
"""

from .connection import get_db, init_db

__all__ = ['get_db', 'init_db']