import os
import time
import threading
from pathlib import Path
from typing import Generator, Optional
from config import config


class LogReader:
    """
    Monitors Minecraft's latest.log file in real-time (like tail -f).
    Detects new lines with ultra-low latency (~10ms) and handles file rotations.
    """

    def __init__(self, log_path: Optional[Path] = None, poll_interval: float = 0.02):
        self.log_path = Path(log_path or config.DEFAULT_MINECRAFT_LOG)
        self.poll_interval = poll_interval
        self._stop_event = threading.Event()
        self._current_pos = 0

    def stop(self) -> None:
        self._stop_event.set()

    def is_running(self) -> bool:
        return not self._stop_event.is_set()

    def stream_lines(self, start_at_end: bool = True) -> Generator[str, None, None]:
        """
        Yields newly appended lines from latest.log.
        If start_at_end is True, skips historical lines and waits for new ones.
        """
        self._stop_event.clear()

        # Wait until the log file exists if not currently present
        while not self.log_path.exists() and not self._stop_event.is_set():
            time.sleep(0.5)

        if self._stop_event.is_set():
            return

        with open(self.log_path, "r", encoding="utf-8", errors="replace") as f:
            if start_at_end:
                f.seek(0, os.SEEK_END)
            self._current_pos = f.tell()

            while not self._stop_event.is_set():
                current_size = self.log_path.stat().st_size if self.log_path.exists() else 0

                # Detect file truncation/rotation (e.g., Minecraft restart)
                if current_size < self._current_pos:
                    f.seek(0, os.SEEK_SET)
                    self._current_pos = 0

                line = f.readline()
                if line:
                    self._current_pos = f.tell()
                    yield line
                else:
                    time.sleep(self.poll_interval)
                    yield ""
