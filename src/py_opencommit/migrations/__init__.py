"""Migrations for OpenCommit."""

from typing import List
from pathlib import Path
import json
import logging
from ..commands.config import Migration, MigrationRunner

logger = logging.getLogger("opencommit")

# Import migrations
from .migrate_00_initialize_config import Migration00InitializeConfig

# Register migrations
migrations: List[Migration] = [
    Migration00InitializeConfig(),
]

def run_migrations():
    """Run all pending migrations."""
    MigrationRunner.run_migrations(migrations)