"""
Unit Tests for Database Models & SQLite Operations
"""
import pytest
from database.models import DatabaseManager


class TestDatabaseManager:
    def test_singleton_instance(self):
        inst1 = DatabaseManager.get_instance()
        inst2 = DatabaseManager.get_instance()
        assert inst1 is inst2

    def test_database_has_items(self, db_manager):
        assert len(db_manager.all_items) > 500

    def test_learn_word_and_lookup(self, db_manager):
        test_word = "Mythoria Test Crystal"
        learned = db_manager.learn_word(test_word, "item")

        norm = "mythoriatestcrystal"
        found = db_manager.find_by_normalized(norm)
        assert found is not None
        assert found.display_name == test_word

        sl = "".join(sorted(norm))
        matches = db_manager.find_by_sorted_letters(sl)
        assert any(m.display_name == test_word for m in matches)

        # Cleanup to keep clean database pristine
        import sqlite3
        conn = sqlite3.connect(db_manager.db_path)
        conn.execute("DELETE FROM minecraft_names WHERE normalized_name = ?", (norm,))
        conn.commit()
        conn.close()
        db_manager._by_normalized.pop(norm, None)

    def test_get_items_by_word_count(self, db_manager):
        single_words = db_manager.get_items_by_word_count(1)
        two_words = db_manager.get_items_by_word_count(2)
        assert len(single_words) > 50
        assert len(two_words) > 50
        assert all(item.word_count == 1 for item in single_words)
        assert all(item.word_count == 2 for item in two_words)
