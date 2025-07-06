"""Admin endpoint to run database migrations - improved version"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text, create_engine
from typing import Dict, List
import re

from app.database import get_db
from app.database.connection import HAS_DATABASE
from app.core.security import get_current_user
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def split_sql_statements(sql: str) -> List[str]:
    """Split SQL into individual statements, handling functions properly"""
    # Remove comments
    sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
    
    # Split by semicolon but not inside function definitions
    statements = []
    current = []
    in_function = False
    
    for line in sql.split('\n'):
        line = line.strip()
        
        # Check for function start
        if 'CREATE OR REPLACE FUNCTION' in line or 'CREATE FUNCTION' in line:
            in_function = True
        
        # Check for function end
        if line == '$$ LANGUAGE plpgsql;' or line.endswith('$$ language \'plpgsql\';'):
            in_function = False
            current.append(line)
            statements.append('\n'.join(current))
            current = []
            continue
        
        # Regular statement end
        if line.endswith(';') and not in_function:
            current.append(line)
            statements.append('\n'.join(current))
            current = []
        else:
            current.append(line)
    
    # Add any remaining
    if current:
        statements.append('\n'.join(current))
    
    return [s.strip() for s in statements if s.strip()]


@router.post("/run-memory-modes-migration-v2")
async def run_memory_modes_migration_v2(
    current_user: Dict = Depends(get_current_user)
):
    """Execute Memory Modes migration with better error handling"""
    
    if not HAS_DATABASE:
        raise HTTPException(503, "Database not configured")
    
    # Read migration SQL
    import os
    migration_path = os.path.join(os.path.dirname(__file__), "..", "..", "database", "memory_modes_schema.sql")
    
    try:
        with open(migration_path, "r") as f:
            migration_sql = f.read()
    except FileNotFoundError:
        raise HTTPException(404, f"Migration file not found: {migration_path}")
    
    results = {
        "total_statements": 0,
        "successful": 0,
        "skipped": 0,
        "failed": 0,
        "tables_created": [],
        "functions_created": [],
        "errors": [],
        "warnings": []
    }
    
    # Create sync engine
    sync_engine = create_engine(settings.database_url)
    
    # Split SQL properly
    statements = split_sql_statements(migration_sql)
    results["total_statements"] = len(statements)
    
    # Execute each statement in its own transaction
    for i, statement in enumerate(statements):
        if not statement or statement.startswith('--'):
            continue
        
        try:
            with sync_engine.begin() as conn:
                conn.execute(text(statement))
                results["successful"] += 1
                
                # Track what was created
                if 'CREATE TABLE' in statement:
                    table_match = re.search(r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?(\w+)', statement)
                    if table_match:
                        results["tables_created"].append(table_match.group(1))
                elif 'CREATE FUNCTION' in statement:
                    func_match = re.search(r'CREATE\s+(?:OR REPLACE\s+)?FUNCTION\s+(\w+)', statement)
                    if func_match:
                        results["functions_created"].append(func_match.group(1))
                        
        except Exception as e:
            error_msg = str(e)
            if "already exists" in error_msg:
                results["skipped"] += 1
                results["warnings"].append(f"Statement {i+1}: Already exists (skipped)")
            else:
                results["failed"] += 1
                results["errors"].append(f"Statement {i+1}: {error_msg[:200]}")
                logger.error(f"Failed statement {i+1}: {statement[:100]}... Error: {error_msg}")
    
    # Verify final state
    try:
        with sync_engine.connect() as conn:
            # Check tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('memory_configs', 'memory_metrics', 'memory_global_config')
            """))
            existing_tables = [row[0] for row in result]
            
            # Check column
            result = conn.execute(text("""
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'chat_sessions' AND column_name = 'memory_mode'
            """))
            memory_mode_exists = result.fetchone() is not None
            
            results["verification"] = {
                "tables_exist": existing_tables,
                "memory_mode_column": memory_mode_exists,
                "success": len(existing_tables) == 3 and memory_mode_exists
            }
    except Exception as e:
        results["verification"] = {"error": str(e)}
    
    # Determine overall status
    if results["failed"] > 0:
        status = "failed"
    elif results["successful"] == 0:
        status = "no_changes"
    elif results["successful"] < results["total_statements"]:
        status = "partial"
    else:
        status = "success"
    
    return {
        "status": status,
        "results": results
    }