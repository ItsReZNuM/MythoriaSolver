"""
Minecraft SMP Chat Game Bot - Main Pipeline
Fixes applied:
  - Skip-Retry bug: clears _active_candidates when game is skipped
  - Random string learning: uses looks_like_random_string filter
  - Delay consistency: check_pending_send runs every iteration (not only on empty yield)
  - Anti-cheat fake wrong answers before correct answer
  - Per-game-type delays from settings
  - Reason logging for all skip/no-answer decisions
"""
import sys
import time
import random
import argparse
import re
from pathlib import Path
from typing import Optional, Dict, Any, List

# Ensure standard UTF-8 stream output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from config import config
from settings import Settings, GAME_TYPE_LABELS
from database.models import DatabaseManager
from solver.router import SolverRouter
from minecraft.log_reader import LogReader
from minecraft.chat_parser import ChatParser, ChatGameQuestionEvent, ChatGameEndEvent
from minecraft.sender import AnswerSender
from collector.chat_game_collector import ChatGameCollector
from stealth import plan_fake_attempts, looks_like_random_string
from menu import run_menu

console = Console(safe_box=True)


class MinecraftChatBot:
    def __init__(self, settings: Settings, log_path: Optional[Path] = None, replay: bool = False):
        self.settings = settings
        self.log_path = Path(log_path or config.DEFAULT_MINECRAFT_LOG)
        self.replay = replay

        self.game_counter = 0

        console.print("[cyan]Initializing Database...[/cyan]")
        self.db = DatabaseManager.get_instance()

        console.print("[cyan]Initializing Solvers and Router...[/cyan]")
        self.router = SolverRouter(self.db)

        console.print("[cyan]Initializing Parser, Sender, and Collector...[/cyan]")
        self.parser = ChatParser()
        self.sender = AnswerSender(
            require_focus=settings.require_focus,
            dry_run=settings.dry_run,
            send_method=settings.send_method,
            cooldown=settings.send_cooldown,
            post_open_chat_delay=getattr(settings, "post_open_chat_delay", 0.25),
            post_type_delay=getattr(settings, "post_type_delay", 0.10),
        )
        self.collector = ChatGameCollector()
        self.log_reader = LogReader(self.log_path)

        self._active_question_event: Optional[ChatGameQuestionEvent] = None
        self._active_candidates: List[Dict[str, Any]] = []
        self._pending_send: Optional[Dict[str, Any]] = None
        # Queue of fake wrong answers to send before the real one
        self._fake_queue: List[str] = []
        self._game_skipped: bool = False
        self._detected_type: str = ""
        self._is_guessing_number: bool = False

    def print_banner(self):
        s = self.settings
        table = Table(box=box.ROUNDED, show_header=False, expand=True)
        table.add_column("Key", style="bold cyan", width=22)
        table.add_column("Value", style="bold white")

        table.add_row("Minecraft Log Path", str(self.log_path))
        table.add_row("Database Items", f"{len(self.db.all_items):,} verified names")
        table.add_row(
            "Answer Frequency",
            f"[bold green]Answer ALL games (1 of 1)[/bold green]"
            if s.answer_ratio == 1
            else f"[bold yellow]1 of every {s.answer_ratio} games ({100/s.answer_ratio:.0f}%)[/bold yellow]",
        )
        table.add_row(
            "Global Delay",
            f"[cyan]{s.global_min_delay:.1f}s - {s.global_max_delay:.1f}s[/cyan] (Randomized)",
        )
        table.add_row(
            "Anti-Cheat Fakes",
            f"[red]{s.stealth.fake_attempts_min}-{s.stealth.fake_attempts_max} wrong attempts[/red]"
            if s.stealth.fake_attempts_max > 0
            else "[green]Disabled[/green]",
        )
        table.add_row(
            "Execution Mode",
            "[yellow]DRY-RUN (No typing)[/yellow]"
            if s.dry_run
            else "[green]LIVE (Active keystrokes)[/green]",
        )
        table.add_row(
            "Require Focus",
            "[green]YES[/green]" if s.require_focus else "[red]NO[/red]",
        )
        table.add_row("Send Method", s.send_method.upper())
        table.add_row("Cooldown", f"{s.send_cooldown:.1f}s")
        table.add_row(
            "Replay Mode",
            "TRUE (Historical Scan)" if self.replay else "FALSE (Tailing live events)",
        )

        stats = self.collector.get_stats()
        if stats.get("total_games", 0) > 0:
            table.add_row(
                "Historical Stats",
                f"Games: {stats['total_games']} | Correct: {stats.get('correct_answers', 0)} "
                f"({stats.get('accuracy_pct', 0.0)}%) | Won: {stats['won_games']} ({stats['win_rate_pct']}%)",
            )

        console.print(
            Panel(
                table,
                title="[bold magenta][*] MINECRAFT SMP CHAT GAME BOT[/bold magenta]",
                border_style="magenta",
            )
        )

    def on_question_received(self, event: ChatGameQuestionEvent):
        self._active_question_event = event
        self._game_skipped = False
        self._fake_queue = []
        self.game_counter += 1

        console.print()
        console.rule(
            f"[bold yellow][GAME #{self.game_counter} DETECTED] [{event.timestamp}][/bold yellow]"
        )
        console.print(f"  [bold]Type:[/bold] [cyan]{event.game_type}[/cyan]")
        console.print(
            f"  [bold]Question:[/bold] [bold white on blue] {event.clean_question} [/bold white on blue]"
        )

        # ── Detect game type ──
        detected_type = self.router.detect_type(event.game_type, event.clean_question)
        self._detected_type = detected_type

        # ── Check if game type is disabled ──
        if not self.settings.is_game_type_enabled(detected_type):
            console.print(
                f"[yellow][SKIPPED] Reason: Game type '{GAME_TYPE_LABELS.get(detected_type, detected_type)}' "
                f"is DISABLED in settings.[/yellow]"
            )
            self._game_skipped = True
            self._active_candidates = []
            self._pending_send = None
            self.collector.start_session(
                timestamp=event.timestamp,
                game_type=event.game_type,
                question=event.clean_question,
                candidates=[],
                answer_sent=None,
            )
            return

        # ── Solve ──
        t0 = time.perf_counter()
        candidates = self.router.solve(event.game_type, event.clean_question)
        solve_time_ms = (time.perf_counter() - t0) * 1000.0

        if not candidates:
            console.print(
                "[red][X] No candidates found.[/red] "
                f"[dim]Reason: All solvers returned empty results for type '{detected_type}'.[/dim]"
            )
            self._active_candidates = []
            self._pending_send = None
            self.collector.start_session(
                timestamp=event.timestamp,
                game_type=event.game_type,
                question=event.clean_question,
                candidates=[],
                answer_sent=None,
            )
            return

        # Display Candidates
        cand_table = Table(box=box.SIMPLE_HEAVY, show_header=True)
        cand_table.add_column("#", style="bold dim", width=3)
        cand_table.add_column("Candidate Answer", style="bold green")
        cand_table.add_column("Score", justify="right", style="cyan")
        cand_table.add_column("Solver", style="magenta")

        for idx, cand in enumerate(candidates[:3], 1):
            cand_table.add_row(
                str(idx),
                cand["answer"],
                f"{cand['score']:.1f}",
                cand.get("solver", "Unknown"),
            )

        console.print(cand_table)
        console.print(f"[dim][*] Solved in {solve_time_ms:.2f} ms[/dim]")

        # ── Skip Ratio Logic ──
        cycle_pos = ((self.game_counter - 1) % self.settings.answer_ratio) + 1
        if self.settings.answer_ratio > 1 and cycle_pos != 1:
            console.print(
                f"[yellow][SKIPPED] Reason: Answer ratio ({cycle_pos}/{self.settings.answer_ratio}). "
                f"Only answering game 1 of every {self.settings.answer_ratio}.[/yellow]"
            )
            self._game_skipped = True
            # BUG FIX: Clear candidates so retry doesn't fire
            self._active_candidates = []
            self._pending_send = None
            self.collector.start_session(
                timestamp=event.timestamp,
                game_type=event.game_type,
                question=event.clean_question,
                candidates=candidates,
                answer_sent=None,
            )
            return

        # ── Prepare answer ──
        top_answer = candidates[0]["answer"]
        if detected_type == "guess_number":
            # For number guessing, keep ALL range candidates in pool for continuous guessing
            self._active_candidates = candidates[1:]
            self._is_guessing_number = True
            fake_answers = []  # No typo fakes for numbers
        else:
            self._active_candidates = candidates[1:self.settings.max_candidate_retries]
            self._is_guessing_number = False
            # ── Plan fake wrong attempts ──
            fake_answers = plan_fake_attempts(top_answer, self.settings.stealth)

        if fake_answers:
            console.print(
                f"[dim][*] Anti-cheat: will send {len(fake_answers)} fake wrong answer(s) first: "
                f"{fake_answers}[/dim]"
            )

        # ── Get per-game-type delay ──
        min_delay, max_delay = self.settings.get_delay(detected_type)

        if self.replay or (min_delay == 0 and max_delay == 0 and not fake_answers):
            # Immediate dispatch for replay or zero delay with no fakes
            self._send_answer_now(top_answer, event, candidates)
        else:
            # Calculate total delay: fake attempts time + human-like delay for correct answer
            fake_total_time = len(fake_answers) * self.settings.stealth.fake_attempt_cooldown
            human_delay = round(random.uniform(min_delay, max_delay), 2)

            # First: send fakes after initial delay
            if fake_answers:
                first_fake_delay = round(random.uniform(min_delay, max_delay), 2)
                self._fake_queue = fake_answers
                self._pending_send = {
                    "answer": top_answer,
                    "target_time": time.time() + first_fake_delay + fake_total_time,
                    "event": event,
                    "candidates": candidates,
                    "delay": first_fake_delay + fake_total_time,
                    "fake_start_time": time.time() + first_fake_delay,
                    "fake_index": 0,
                }
                console.print(
                    f"[dim][*] Stealth plan: {first_fake_delay:.2f}s wait -> "
                    f"{len(fake_answers)} fakes ({fake_total_time:.1f}s) -> correct answer[/dim]"
                )
            else:
                self._pending_send = {
                    "answer": top_answer,
                    "target_time": time.time() + human_delay,
                    "event": event,
                    "candidates": candidates,
                    "delay": human_delay,
                }
                console.print(
                    f"[dim][*] Anti-ban stealth delay: waiting {human_delay:.2f}s before typing answer...[/dim]"
                )

    def _send_answer_now(self, top_answer: str, event: ChatGameQuestionEvent, candidates: list):
        self.collector.start_session(
            timestamp=event.timestamp,
            game_type=event.game_type,
            question=event.clean_question,
            candidates=candidates,
            answer_sent=top_answer,
        )
        sent = self.sender.send_chat_message(top_answer)
        if sent:
            console.print(
                f"[bold green][OK] Typed and submitted:[/bold green] [bold white]{top_answer}[/bold white]"
            )
        else:
            if not self.sender.is_minecraft_focused() and self.settings.require_focus:
                console.print(
                    "[yellow][!] Not sent: Minecraft window not in foreground.[/yellow]"
                )

    def check_pending_send(self):
        """Execute delayed answer / fake attempts if delay elapsed and game is still active."""
        if self._pending_send is None:
            return

        now = time.time()

        # ── Handle fake wrong attempts ──
        if self._fake_queue and "fake_start_time" in self._pending_send:
            fake_start = self._pending_send["fake_start_time"]
            fake_idx = self._pending_send.get("fake_index", 0)
            cooldown = self.settings.stealth.fake_attempt_cooldown

            # Time for the next fake?
            next_fake_time = fake_start + (fake_idx * cooldown)
            if now >= next_fake_time and fake_idx < len(self._fake_queue):
                if self._active_question_event is not None:
                    fake_msg = self._fake_queue[fake_idx]
                    sent = self.sender.send_chat_message(fake_msg)
                    if sent:
                        console.print(
                            f"[red][FAKE #{fake_idx+1}] Sent wrong answer:[/red] [dim]{fake_msg}[/dim]"
                        )
                    self._pending_send["fake_index"] = fake_idx + 1

                    # If all fakes sent, recalculate correct answer target time
                    if fake_idx + 1 >= len(self._fake_queue):
                        self._fake_queue = []
                        remaining_delay = cooldown  # One more cooldown after last fake
                        self._pending_send["target_time"] = now + remaining_delay
                else:
                    # Game ended during fakes
                    console.print(
                        "[yellow][!] Game ended during fake attempts. Cancelled.[/yellow]"
                    )
                    self._pending_send = None
                    self._fake_queue = []
                    return

        # ── Handle correct answer ──
        if self._fake_queue:
            return  # Still sending fakes

        if now >= self._pending_send["target_time"]:
            item = self._pending_send
            self._pending_send = None

            if self._active_question_event is not None:
                top_ans = item["answer"]
                self.collector.start_session(
                    timestamp=item["event"].timestamp,
                    game_type=item["event"].game_type,
                    question=item["event"].clean_question,
                    candidates=item["candidates"],
                    answer_sent=top_ans,
                )
                sent = self.sender.send_chat_message(top_ans)
                if sent:
                    console.print(
                        f"[bold green][OK] Typed and submitted ({item['delay']:.2f}s delay):[/bold green] "
                        f"[bold white]{top_ans}[/bold white]"
                    )
                else:
                    if not self.sender.is_minecraft_focused() and self.settings.require_focus:
                        console.print(
                            "[yellow][!] Not sent: Minecraft window not in foreground.[/yellow]"
                        )
            else:
                console.print(
                    "[yellow][!] Reason: Game ended before stealth delay elapsed. Correct answer cancelled.[/yellow]"
                )

    def check_candidate_retry(self):
        """Send next candidate if the game is still active and cooldown elapsed."""
        # BUG FIX: Skip if game was skipped by ratio or disabled
        if self._game_skipped:
            return

        if (
            self._active_question_event is not None
            and self._pending_send is None
            and not self._fake_queue
            and self._active_candidates
            and (time.time() - self.sender.last_send_time >= self.sender.cooldown)
        ):
            next_cand = self._active_candidates.pop(0)
            next_answer = next_cand["answer"]

            if self._is_guessing_number:
                console.print(
                    f"[bold cyan][NUMBER GUESS][/bold cyan] [bold white]{next_answer}[/bold white] "
                    f"[dim]({len(self._active_candidates)} unguessed remaining in pool)[/dim]"
                )
            else:
                console.print(
                    f"[bold cyan][RETRY NEXT CANDIDATE][/bold cyan] [bold white]{next_answer}[/bold white]"
                )

            self.collector.record_answer_sent(next_answer)
            sent = self.sender.send_chat_message(next_answer)
            if sent:
                if self._is_guessing_number:
                    console.print(
                        f"[bold green][OK] Typed number guess:[/bold green] [bold white]{next_answer}[/bold white]"
                    )
                else:
                    console.print(
                        f"[bold green][OK] Typed candidate retry:[/bold green] [bold white]{next_answer}[/bold white]"
                    )

    def _handle_other_player_guess(self, raw_line: str):
        """When in 'guess_number' game, detect other players' guesses and eliminate them from candidate pool."""
        if not self._is_guessing_number or self._active_question_event is None:
            return

        clean = raw_line.split("[CHAT]", 1)[-1] if "[CHAT]" in raw_line else raw_line
        match = re.search(r"(?:▶|:)\s*(\d+)\s*$", clean)
        if match:
            guessed_num = match.group(1)
            before_len = len(self._active_candidates)
            self._active_candidates = [
                c for c in self._active_candidates if c["answer"] != guessed_num
            ]

            # If pending send is going to send this number, switch to another candidate
            if self._pending_send and self._pending_send.get("answer") == guessed_num:
                if self._active_candidates:
                    new_cand = self._active_candidates.pop(0)
                    new_pick = new_cand["answer"]
                    self._pending_send["answer"] = new_pick
                    console.print(
                        f"[dim][*] Number {guessed_num} was guessed by another player. Switched our pending guess to {new_pick}[/dim]"
                    )
                else:
                    self._pending_send = None
            elif len(self._active_candidates) < before_len:
                console.print(
                    f"[dim][*] Eliminated #{guessed_num} (guessed by another player). {len(self._active_candidates)} unguessed remaining in pool.[/dim]"
                )

    def on_game_ended(self, event: ChatGameEndEvent):
        console.print()
        duration_str = (
            f"in {event.duration_seconds:.2f}s"
            if event.duration_seconds is not None
            else ""
        )
        if event.timeout:
            console.print(
                f"[bold red][TIMEOUT] CHAT GAME ENDED[/bold red] {duration_str}"
            )
        else:
            console.print(
                f"[bold green][WINNER][/bold green] [bold cyan]{event.winner}[/bold cyan] {duration_str}"
            )

        # Cancel any pending send / fake queue
        if self._pending_send is not None:
            console.print(
                "[yellow][!] Reason: Game concluded before stealth delay elapsed. Cancelled typing.[/yellow]"
            )
            self._pending_send = None
            self._fake_queue = []

        if event.answer:
            console.print(
                f"  [bold]Correct Answer was:[/bold] [bold green]{event.answer}[/bold green]"
            )
            # 1. Self-learning for trivia solver
            if (
                self._active_question_event
                and "answer" in self._active_question_event.game_type.lower()
            ):
                self.router.trivia_solver.learn_answer(
                    self._active_question_event.clean_question, event.answer
                )
                console.print(
                    f"[bold green][+ LEARNED TRIVIA][/bold green] Saved Q&A: "
                    f"'{self._active_question_event.clean_question}' -> '{event.answer}'"
                )

            # 2. Self-learning for words/items/blocks (with improved filters)
            elif self.settings.auto_learn_words:
                answer_text = event.answer.strip()
                skip_reason = None

                if answer_text.isdigit():
                    skip_reason = "numeric answer"
                elif answer_text.lower() in {"yes", "no"}:
                    skip_reason = "yes/no answer"
                elif len(answer_text) < self.settings.auto_learn_min_length:
                    skip_reason = f"too short ({len(answer_text)} < {self.settings.auto_learn_min_length})"
                elif self.settings.auto_learn_filter_random and looks_like_random_string(answer_text):
                    # BUG FIX: Don't learn random strings like 'OnpjAm', '84H2heqtC'
                    skip_reason = f"looks like random string ('{answer_text}')"

                if skip_reason:
                    console.print(
                        f"[dim][*] Not learning '{answer_text}': {skip_reason}[/dim]"
                    )
                else:
                    learned = self.db.learn_word(answer_text, item_type="learned_from_server")
                    if learned:
                        console.print(
                            f"[bold green][+ LEARNED NEW WORD][/bold green] Added "
                            f"'[bold white]{answer_text}[/bold white]' to database!"
                        )

        record = self.collector.complete_session(
            winner=event.winner,
            duration=event.duration_seconds,
            actual_answer=event.answer,
        )
        if record and record.our_bot_won:
            console.print("[bold yellow][***] OUR BOT WON THE GAME! [***][/bold yellow]")

        self._active_question_event = None
        self._active_candidates = []
        self._game_skipped = False
        self._is_guessing_number = False

    def run(self):
        self.print_banner()
        console.print(
            "\n[bold green][*] Monitoring chat games... Press Ctrl+C to exit.[/bold green]\n"
        )

        try:
            for line in self.log_reader.stream_lines(start_at_end=not self.replay):
                # Check pending sends and retry attempts on every iteration
                self.check_pending_send()
                self.check_candidate_retry()

                if line:
                    event = self.parser.parse_line(line)
                    if isinstance(event, ChatGameQuestionEvent):
                        self.on_question_received(event)
                    elif isinstance(event, ChatGameEndEvent):
                        self.on_game_ended(event)
                    elif self._is_guessing_number:
                        self._handle_other_player_guess(line)

                if self.replay:
                    time.sleep(0.005)

        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping Minecraft Chat Bot... Goodbye![/yellow]")
            self.log_reader.stop()


def main():
    parser = argparse.ArgumentParser(description="Minecraft SMP Chat Game Bot")
    parser.add_argument(
        "--replay", action="store_true", help="Replay historical log file"
    )
    parser.add_argument(
        "--log-path", type=str, default=None, help="Custom Minecraft latest.log path"
    )
    parser.add_argument(
        "--no-menu", action="store_true", help="Skip interactive startup menu"
    )

    args = parser.parse_args()

    # Load persistent settings
    settings = Settings.load()

    # Show game-style menu unless skipped
    if not args.no_menu and not args.replay and sys.stdin.isatty():
        action = run_menu(settings)
        if action == "exit":
            return
    else:
        console.print("[dim]Skipping menu (--no-menu or replay mode).[/dim]")

    bot = MinecraftChatBot(
        settings=settings,
        log_path=Path(args.log_path) if args.log_path else None,
        replay=args.replay,
    )
    bot.run()


if __name__ == "__main__":
    main()
