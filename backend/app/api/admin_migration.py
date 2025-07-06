"""Admin endpoint to run database migrations"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text, create_engine
from typing import Dict, List

from app.database import get_db
from app.database.connection import engine, HAS_DATABASE
from app.core.security import get_current_user
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/run-memory-modes-migration")
async def run_memory_modes_migration(
    current_user: Dict = Depends(get_current_user)
):
    """Execute Memory Modes migration (admin only)"""
    
    # Check if user is admin (you can add proper admin check here)
    # For now, any authenticated user can run this
    
    if not HAS_DATABASE:
        raise HTTPException(503, "Database not configured")
    
    try:
        # Read migration SQL
        import os
        migration_path = os.path.join(os.path.dirname(__file__), "..", "..", "database", "memory_modes_schema.sql")
        with open(migration_path, "r") as f:
            migration_sql = f.read()
        
        results = {
            "tables_created": [],
            "errors": [],
            "warnings": []
        }
        
        # Create sync engine for migration
        sync_engine = create_engine(settings.database_url)
        
        # Execute migration
        with sync_engine.connect() as conn:
            # Split by statements and execute each
            statements = [s.strip() for s in migration_sql.split(';') if s.strip()]
            
            for statement in statements:
                if statement:
                    try:
                        conn.execute(text(statement))
                        conn.commit()
                    except Exception as e:
                        error_msg = str(e)
                        if "already exists" in error_msg:
                            results["warnings"].append(f"Object already exists (skipped)")
                        else:
                            results["errors"].append(error_msg[:200])  # Truncate long errors
            
            # Verify what was created
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('memory_configs', 'memory_metrics', 'memory_global_config')
            """))
            
            results["tables_created"] = [row[0] for row in result]
            
            # Check memory_mode column
            result = conn.execute(text("""
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'chat_sessions' 
                AND column_name = 'memory_mode'
            """))
            
            if result.fetchone():
                results["memory_mode_column_added"] = True
            
            # Check global config
            result = conn.execute(text("""
                SELECT mode, config 
                FROM memory_global_config 
                WHERE is_active = true
            """))
            config = result.fetchone()
            
            if config:
                results["global_config"] = {
                    "mode": config[0],
                    "active": True
                }
        
        return {
            "status": "success" if not results["errors"] else "partial",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise HTTPException(500, f"Migration failed: {str(e)}")


@router.get("/check-memory-tables")
async def check_memory_tables(
    current_user: Dict = Depends(get_current_user)
):
    """Check if Memory Modes tables exist"""
    
    if not HAS_DATABASE:
        raise HTTPException(503, "Database not configured")
    
    try:
        # Create sync engine for check
        sync_engine = create_engine(settings.database_url)
        
        with sync_engine.connect() as conn:
            # Check tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('memory_configs', 'memory_metrics', 'memory_global_config')
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            
            # Check column
            result = conn.execute(text("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns 
                WHERE table_name = 'chat_sessions' 
                AND column_name = 'memory_mode'
            """))
            column = result.fetchone()
            
            # Check functions
            result = conn.execute(text("""
                SELECT routine_name 
                FROM information_schema.routines 
                WHERE routine_schema = 'public' 
                AND routine_name IN ('get_session_memory_config', 'update_memory_metrics')
            """))
            functions = [row[0] for row in result]
            
            return {
                "tables": tables,
                "memory_mode_column": {
                    "exists": column is not None,
                    "type": column[1] if column else None,
                    "default": column[2] if column else None
                },
                "functions": functions,
                "ready": len(tables) == 3 and column is not None
            }
    
    except Exception as e:
        logger.error(f"Check failed: {e}")
        raise HTTPException(500, f"Check failed: {str(e)}")