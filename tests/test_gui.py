"""
Integration Tests for Modern CustomTkinter GUI
Tests window initialization, 0ms tab switching, settings population, and event bridge.
"""
import pytest
import gui
from ui.tabs import (
    DashboardTab,
    GeneralTab,
    SolversTab,
    StealthTab,
    TabchiTab,
    SandboxTab,
)


class TestGUI:
    @pytest.fixture(autouse=True)
    def setup_and_teardown_app(self):
        self.app = gui.MythoriaGUI()
        self.app.update()
        yield
        try:
            self.app.destroy()
        except Exception:
            pass

    def test_gui_instantiation_and_tabs(self):
        assert self.app.current_tab == "dashboard"
        assert len(self.app.tab_frames) == 6
        assert isinstance(self.app.tab_frames["dashboard"], DashboardTab)
        assert isinstance(self.app.tab_frames["general"], GeneralTab)
        assert isinstance(self.app.tab_frames["solvers"], SolversTab)
        assert isinstance(self.app.tab_frames["stealth"], StealthTab)
        assert isinstance(self.app.tab_frames["tabchi"], TabchiTab)
        assert isinstance(self.app.tab_frames["sandbox"], SandboxTab)

    def test_tab_switching_mapping_contract(self):
        tabs = ["general", "solvers", "stealth", "tabchi", "sandbox", "dashboard"]
        for tid in tabs:
            self.app.switch_tab(tid)
            self.app.update()
            
            # Verify exact target is mapped, and other 5 are unmapped
            for check_tid, frame in self.app.tab_frames.items():
                pw = getattr(frame, "_parent_frame", frame)
                if check_tid == tid:
                    assert pw.winfo_ismapped() == 1, f"Tab {tid} should be mapped"
                else:
                    assert pw.winfo_ismapped() == 0, f"Tab {check_tid} should be unmapped"

    def test_event_queue_handling(self):
        # Simulate bot events dispatched to GUI
        self.app._handle_bot_event("question", {
            "game_number": 99,
            "raw_type": "math",
            "clean_question": "5 + 5",
            "detected_type": "math",
        })
        assert self.app.stats_games == 1
        assert self.app.tab_dashboard.card_games.cget("text") == "1"

        self.app._handle_bot_event("game_ended", {
            "winner": self.app.settings.player_username,
            "answer": "10",
            "our_won": True,
            "duration": 2.1,
        })
        assert self.app.stats_wins == 1

        self.app._handle_bot_event("advert_sent", {
            "message": "All view ah",
        })
        assert self.app.stats_ads == 1
        assert self.app.tab_dashboard.card_ads.cget("text") == "1"

    def test_append_and_clear_logs(self):
        self.app.append_log("TEST", "Sample integration test log entry")
        content = self.app.tab_dashboard.txt_log.get("1.0", "end")
        assert "Sample integration test log entry" in content

        self.app.clear_logs()
        cleared_content = self.app.tab_dashboard.txt_log.get("1.0", "end")
        assert "Logs cleared." in cleared_content
