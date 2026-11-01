"""
Pytest Shared Fixtures for MythoriaSolver Test Suite
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure root workspace directory is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from settings import Settings, GameTypeDelay, StealthSettings, TabchiSettings
from database.models import DatabaseManager
from solver.router import SolverRouter


@pytest.fixture(scope="session")
def db_manager(tmp_path_factory):
    """Provides a DatabaseManager instance backed by an isolated copy of the database."""
    import shutil
    temp_dir = tmp_path_factory.mktemp("db_test")
    temp_db_path = temp_dir / "minecraft_clean.db"
    orig_db = ROOT_DIR / "database" / "minecraft_clean.db"
    shutil.copy2(orig_db, temp_db_path)
    return DatabaseManager(db_path=temp_db_path)


@pytest.fixture(scope="session")
def solver_router(db_manager):
    """Provides a SolverRouter instance wired to the test DatabaseManager."""
    return SolverRouter(db_manager=db_manager)


@pytest.fixture
def mock_settings(tmp_path):
    """Provides an isolated Settings instance configured to write to a temp directory."""
    temp_settings_file = tmp_path / "settings.json"
    s = Settings(
        player_username="TestPlayer",
        minecraft_log_path=str(tmp_path / "latest.log"),
        dry_run=True,
        require_focus=False,
        send_method="paste",
        chat_key="t",
        send_cooldown=3.0,
        answer_ratio=1,
    )
    return s
