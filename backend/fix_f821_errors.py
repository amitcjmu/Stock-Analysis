#!/usr/bin/env python3
"""Fix F821 undefined name errors in Python files."""

import os
import re
from collections import defaultdict

# Common import mappings for undefined names
IMPORT_MAPPINGS = {
    # Standard library
    'logger': 'import logging\nlogger = logging.getLogger(__name__)',
    'json': 'import json',
    'os': 'import os',
    'datetime': 'from datetime import datetime',
    'timezone': 'from datetime import timezone',
    'timedelta': 'from datetime import timedelta',
    'uuid': 'import uuid',
    'UUID': 'from uuid import UUID',
    'mock': 'from unittest import mock',
    'Mock': 'from unittest.mock import Mock',
    'patch': 'from unittest.mock import patch',
    'AsyncMock': 'from unittest.mock import AsyncMock',
    'MagicMock': 'from unittest.mock import MagicMock',
    
    # Typing imports
    'Any': 'from typing import Any',
    'Dict': 'from typing import Dict',
    'List': 'from typing import List',
    'Optional': 'from typing import Optional',
    'Union': 'from typing import Union',
    'Tuple': 'from typing import Tuple',
    'Set': 'from typing import Set',
    'Type': 'from typing import Type',
    'TypeVar': 'from typing import TypeVar',
    'Generic': 'from typing import Generic',
    'Callable': 'from typing import Callable',
    'Iterator': 'from typing import Iterator',
    'Sequence': 'from typing import Sequence',
    'Mapping': 'from typing import Mapping',
    'Awaitable': 'from typing import Awaitable',
    'AsyncIterator': 'from typing import AsyncIterator',
    'Protocol': 'from typing import Protocol',
    'TypedDict': 'from typing import TypedDict',
    'Literal': 'from typing import Literal',
    'ClassVar': 'from typing import ClassVar',
    'Final': 'from typing import Final',
    'cast': 'from typing import cast',
    'overload': 'from typing import overload',
    'TYPE_CHECKING': 'from typing import TYPE_CHECKING',
    
    # Common third-party
    'HTTPException': 'from fastapi import HTTPException',
    'Depends': 'from fastapi import Depends',
    'APIRouter': 'from fastapi import APIRouter',
    'Request': 'from fastapi import Request',
    'Response': 'from fastapi import Response',
    'status': 'from fastapi import status',
    'Query': 'from fastapi import Query',
    'Path': 'from fastapi import Path',
    'Body': 'from fastapi import Body',
    'Form': 'from fastapi import Form',
    'File': 'from fastapi import File',
    'UploadFile': 'from fastapi import UploadFile',
    'BackgroundTasks': 'from fastapi import BackgroundTasks',
    'WebSocket': 'from fastapi import WebSocket',
    'WebSocketDisconnect': 'from fastapi import WebSocketDisconnect',
    
    # SQLAlchemy
    'select': 'from sqlalchemy import select',
    'update': 'from sqlalchemy import update',
    'delete': 'from sqlalchemy import delete',
    'insert': 'from sqlalchemy import insert',
    'and_': 'from sqlalchemy import and_',
    'or_': 'from sqlalchemy import or_',
    'func': 'from sqlalchemy import func',
    'text': 'from sqlalchemy import text',
    'Column': 'from sqlalchemy import Column',
    'String': 'from sqlalchemy import String',
    'Integer': 'from sqlalchemy import Integer',
    'Boolean': 'from sqlalchemy import Boolean',
    'DateTime': 'from sqlalchemy import DateTime',
    'Float': 'from sqlalchemy import Float',
    'Text': 'from sqlalchemy import Text',
    'ForeignKey': 'from sqlalchemy import ForeignKey',
    'relationship': 'from sqlalchemy.orm import relationship',
    'Session': 'from sqlalchemy.orm import Session',
    'sessionmaker': 'from sqlalchemy.orm import sessionmaker',
    'declarative_base': 'from sqlalchemy.ext.declarative import declarative_base',
    
    # Pydantic
    'BaseModel': 'from pydantic import BaseModel',
    'Field': 'from pydantic import Field',
    'validator': 'from pydantic import validator',
    'root_validator': 'from pydantic import root_validator',
    'ValidationError': 'from pydantic import ValidationError',
    'ConfigDict': 'from pydantic import ConfigDict',
    
    # pytest
    'pytest': 'import pytest',
    
    # asyncio
    'asyncio': 'import asyncio',
    
    # CrewAI
    'Agent': 'from crewai import Agent',
    'Task': 'from crewai import Task',
    'Crew': 'from crewai import Crew',
    'Process': 'from crewai import Process',
    
    # Common app imports
    'settings': 'from app.core.config import settings',
    'get_db': 'from app.core.database import get_db',
    'get_current_user': 'from app.core.auth import get_current_user',
}

# Project-specific imports (will be detected from codebase)
PROJECT_IMPORTS = {
    'SessionFlowCompatibilityService': 'from app.services.session_flow_compatibility import SessionFlowCompatibilityService',
    'DataImport': 'from app.models.data_import import DataImport',
    'RawImportRecord': 'from app.models.data_import import RawImportRecord',
    'Engagement': 'from app.models.engagement import Engagement',
    'Asset': 'from app.models.asset import Asset',
    'DiscoveryFlowState': 'from app.models.discovery_flow_state import DiscoveryFlowState',
    'UnifiedDiscoveryFlowState': 'from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState',
    'SixRAgentOrchestrator': 'from app.services.agents.sixr_orchestrator import SixRAgentOrchestrator',
    'CrewAIService': 'from app.services.crewai_service import CrewAIService',
    'master_orchestrator': 'from app.services.master_flow_orchestrator import master_orchestrator',
    'agent_ui_bridge': 'from app.services.agent_ui_bridge import agent_ui_bridge',
    'client_context_manager': 'from app.services.client_context_manager import client_context_manager',
    'crewai_flow_service': 'from app.services.crewai_flow_service import crewai_flow_service',
}

def parse_ruff_output(output):
    """Parse ruff output to extract file paths and undefined names."""
    errors = defaultdict(set)
    
    # Pattern to match ruff F821 errors
    pattern = r'(.+?):(\d+):(\d+): F821 Undefined name `(.+?)`'
    
    for match in re.finditer(pattern, output):
        file_path = match.group(1)
        undefined_name = match.group(4)
        errors[file_path].add(undefined_name)
    
    return errors

def get_import_statement(name):
    """Get the import statement for an undefined name."""
    if name in IMPORT_MAPPINGS:
        return IMPORT_MAPPINGS[name]
    elif name in PROJECT_IMPORTS:
        return PROJECT_IMPORTS[name]
    else:
        # Try to guess common patterns
        if name.endswith('Schema') or name.endswith('Create') or name.endswith('Update'):
            return f'from app.schemas import {name}'
        elif name.endswith('Service'):
            return f'from app.services import {name}'
        elif name.endswith('Model'):
            return f'from app.models import {name}'
        elif name.endswith('Repository'):
            return f'from app.repositories import {name}'
        elif name.endswith('Handler'):
            return f'from app.handlers import {name}'
        elif name.endswith('Error') or name.endswith('Exception'):
            return f'from app.core.exceptions import {name}'
        else:
            return None

def fix_file(file_path, undefined_names):
    """Fix undefined names in a single file."""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Find where to insert imports (after existing imports)
    import_end_idx = 0
    for i, line in enumerate(lines):
        if line.strip() and not (line.startswith('import ') or line.startswith('from ') or line.startswith('#') or line.strip() == '"""' or line.strip().startswith('"""')):
            import_end_idx = i
            break
        elif line.startswith('import ') or line.startswith('from '):
            import_end_idx = i + 1
    
    # Collect needed imports
    imports_to_add = []
    for name in undefined_names:
        import_stmt = get_import_statement(name)
        if import_stmt:
            # Check if import already exists
            if import_stmt not in content:
                imports_to_add.append(import_stmt)
        else:
            print(f"  Warning: No import mapping found for '{name}' in {file_path}")
    
    if imports_to_add:
        # Sort imports
        imports_to_add = sorted(set(imports_to_add))
        
        # Insert imports
        for import_stmt in reversed(imports_to_add):
            lines.insert(import_end_idx, import_stmt)
        
        # Add blank line after imports if needed
        if import_end_idx > 0 and lines[import_end_idx + len(imports_to_add)].strip():
            lines.insert(import_end_idx + len(imports_to_add), '')
        
        # Write back
        with open(file_path, 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"Fixed {file_path}: Added {len(imports_to_add)} imports")
        return True
    
    return False

def main():
    # Run ruff to get all F821 errors
    print("Running ruff check for F821 errors...")
    import subprocess
    
    result = subprocess.run(
        ['docker', 'run', '--rm', '-v', f'{os.getcwd()}:/app', '-w', '/app', 'backend-lint', 'ruff', 'check', '.', '--select', 'F821'],
        capture_output=True,
        text=True
    )
    
    errors = parse_ruff_output(result.stdout)
    
    if not errors:
        print("No F821 errors found!")
        return
    
    print(f"Found F821 errors in {len(errors)} files")
    
    # Fix each file
    fixed_count = 0
    for file_path, undefined_names in errors.items():
        print(f"\nProcessing {file_path}...")
        print(f"  Undefined names: {', '.join(sorted(undefined_names))}")
        
        if fix_file(file_path, undefined_names):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} files")
    
    # Run ruff again to check remaining errors
    print("\nRunning ruff check again...")
    result = subprocess.run(
        ['docker', 'run', '--rm', '-v', f'{os.getcwd()}:/app', '-w', '/app', 'backend-lint', 'ruff', 'check', '.', '--select', 'F821'],
        capture_output=True,
        text=True
    )
    
    remaining_errors = parse_ruff_output(result.stdout)
    if remaining_errors:
        print(f"\nRemaining errors in {len(remaining_errors)} files:")
        for file_path, names in remaining_errors.items():
            print(f"  {file_path}: {', '.join(sorted(names))}")
    else:
        print("\nAll F821 errors fixed!")

if __name__ == '__main__':
    main()