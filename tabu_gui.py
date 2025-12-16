"""
Tabu Search Attack GUI - Dark Theme
Visualizes the state recovery attack in real-time
"""

import tkinter as tk
from tkinter import ttk, messagebox
from tabu_logic import TabuCracker, generate_challenge
import queue
import numpy as np


class TabuSearchFrame(tk.Frame):
    """
    GUI for Tabu Search State Recovery Attack
    Dark theme with real-time S-box visualization
    """

    # Dark theme colors
    BG_COLOR = "#2b2b2b"
    FG_COLOR = "#00ff00"
    BUTTON_BG = "#3c3c3c"
    BUTTON_FG = "#00ff00"
    LABEL_BG = "#1e1e1e"
    MATCH_COLOR = "#00ff00"  # Green for matches
    MISMATCH_COLOR = "#ff0000"  # Red for mismatches
    NEUTRAL_COLOR = "#404040"  # Dark gray for neutral

    def __init__(self, parent):
        super().__init__(parent, bg=self.BG_COLOR)

        self.cracker = None
        self.target_state = None
        self.update_queue = queue.Queue()
        self.running = False

        self._setup_ui()
        self._start_update_polling()

    def _setup_ui(self):
        """Setup the user interface"""
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)

        self._setup_controls()
        self._setup_visualization()
        self._setup_stats()

    def _setup_controls(self):
        """Setup control panel"""
        control_frame = tk.LabelFrame(
            self,
            text="Attack Controls",
            bg=self.BG_COLOR,
            fg=self.FG_COLOR,
            font=("Courier", 12, "bold"),
        )
        control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        tk.Label(
            control_frame,
            text="Target N:",
            bg=self.BG_COLOR,
            fg=self.FG_COLOR,
            font=("Courier", 10),
        ).pack(anchor="w", padx=5, pady=5)

        self.n_var = tk.StringVar(value="64")
        n_combo = ttk.Combobox(
            control_frame,
            textvariable=self.n_var,
            values=["64", "128", "256"],
            state="readonly",
            width=10,
        )
        n_combo.pack(padx=5, pady=5)

        tk.Label(
            control_frame,
            text="Keystream Length:",
            bg=self.BG_COLOR,
            fg=self.FG_COLOR,
            font=("Courier", 10),
        ).pack(anchor="w", padx=5, pady=5)

        self.keystream_length_var = tk.StringVar(value="100")
        keystream_entry = tk.Entry(
            control_frame,
            textvariable=self.keystream_length_var,
            bg=self.BUTTON_BG,
            fg=self.FG_COLOR,
            width=10,
        )
        keystream_entry.pack(padx=5, pady=5)

        tk.Label(
            control_frame,
            text="Max Iterations:",
            bg=self.BG_COLOR,
            fg=self.FG_COLOR,
            font=("Courier", 10),
        ).pack(anchor="w", padx=5, pady=5)

        self.max_iter_var = tk.StringVar(value="5000")
        iter_entry = tk.Entry(
            control_frame,
            textvariable=self.max_iter_var,
            bg=self.BUTTON_BG,
            fg=self.FG_COLOR,
            width=10,
        )
        iter_entry.pack(padx=5, pady=5)

        self.start_button = tk.Button(
            control_frame,
            text="Generate Target & Start",
            command=self._start_attack,
            bg=self.BUTTON_BG,
            fg=self.BUTTON_FG,
            font=("Courier", 10, "bold"),
            relief=tk.RAISED,
        )
        self.start_button.pack(padx=5, pady=10, fill=tk.X)

        self.stop_button = tk.Button(
            control_frame,
            text="Stop Attack",
            command=self._stop_attack,
            bg=self.BUTTON_BG,
            fg="#ff4444",
            font=("Courier", 10, "bold"),
            relief=tk.RAISED,
            state=tk.DISABLED,
        )
        self.stop_button.pack(padx=5, pady=5, fill=tk.X)

        info_frame = tk.LabelFrame(
            control_frame,
            text="Z2 Config",
            bg=self.BG_COLOR,
            fg=self.FG_COLOR,
            font=("Courier", 9),
        )
        info_frame.pack(padx=5, pady=10, fill=tk.BOTH)

        info_text = (
            "• Fitness: Byte Match\n"
            "• Neighborhood: 50% Swaps\n"
            "• Tabu Tenure: N(N-1)/4\n"
            "• Aspiration: Best"
        )
        tk.Label(
            info_frame,
            text=info_text,
            bg=self.BG_COLOR,
            fg="#888888",
            font=("Courier", 8),
            justify=tk.LEFT,
        ).pack(padx=5, pady=5)

    def _setup_visualization(self):
        """Setup S-box visualization canvas"""
        viz_frame = tk.LabelFrame(
            self,
            text="S-Box State (Green=Match)",
            bg=self.BG_COLOR,
            fg=self.FG_COLOR,
            font=("Courier", 12, "bold"),
        )
        viz_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.canvas = tk.Canvas(
            viz_frame, bg=self.LABEL_BG, width=640, height=640, highlightthickness=0
        )
        self.canvas.pack(padx=10, pady=10)
        self.cell_rects = []

    def _setup_stats(self):
        """Setup statistics panel"""
        stats_frame = tk.LabelFrame(
            self,
            text="Statistics",
            bg=self.BG_COLOR,
            fg=self.FG_COLOR,
            font=("Courier", 12, "bold"),
        )
        stats_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

        tk.Label(
            stats_frame,
            text="Iteration:",
            bg=self.BG_COLOR,
            fg=self.FG_COLOR,
            font=("Courier", 10),
        ).pack(anchor="w", padx=5, pady=5)
        self.iter_label = tk.Label(
            stats_frame,
            text="0",
            bg=self.LABEL_BG,
            fg=self.FG_COLOR,
            font=("Courier", 14, "bold"),
        )
        self.iter_label.pack(padx=5, pady=5, fill=tk.X)

        tk.Label(
            stats_frame,
            text="Current Fitness:",
            bg=self.BG_COLOR,
            fg=self.FG_COLOR,
            font=("Courier", 10),
        ).pack(anchor="w", padx=5, pady=5)
        self.fitness_label = tk.Label(
            stats_frame,
            text="0 / 0 (0.0%)",
            bg=self.LABEL_BG,
            fg=self.FG_COLOR,
            font=("Courier", 12, "bold"),
        )
        self.fitness_label.pack(padx=5, pady=5, fill=tk.X)

        tk.Label(
            stats_frame,
            text="Best Fitness:",
            bg=self.BG_COLOR,
            fg=self.FG_COLOR,
            font=("Courier", 10),
        ).pack(anchor="w", padx=5, pady=5)
        self.best_fitness_label = tk.Label(
            stats_frame,
            text="0 / 0 (0.0%)",
            bg=self.LABEL_BG,
            fg="#00ffff",
            font=("Courier", 12, "bold"),
        )
        self.best_fitness_label.pack(padx=5, pady=5, fill=tk.X)

        tk.Label(
            stats_frame,
            text="Tabu List Size:",
            bg=self.BG_COLOR,
            fg=self.FG_COLOR,
            font=("Courier", 10),
        ).pack(anchor="w", padx=5, pady=5)
        self.tabu_label = tk.Label(
            stats_frame,
            text="0",
            bg=self.LABEL_BG,
            fg=self.FG_COLOR,
            font=("Courier", 12, "bold"),
        )
        self.tabu_label.pack(padx=5, pady=5, fill=tk.X)

        tk.Label(
            stats_frame,
            text="Swaps/Iteration:",
            bg=self.BG_COLOR,
            fg=self.FG_COLOR,
            font=("Courier", 10),
        ).pack(anchor="w", padx=5, pady=5)
        self.swaps_label = tk.Label(
            stats_frame,
            text="0",
            bg=self.LABEL_BG,
            fg=self.FG_COLOR,
            font=("Courier", 12, "bold"),
        )
        self.swaps_label.pack(padx=5, pady=5, fill=tk.X)

    def _draw_grid(self, N):
        """Draw initial grid for N elements"""
        self.canvas.delete("all")
        self.cell_rects = []
        cols = int(np.ceil(np.sqrt(N)))
        rows = int(np.ceil(N / cols))
        canvas_width = 640
        canvas_height = 640
        cell_width = canvas_width // cols
        cell_height = canvas_height // rows

        for idx in range(N):
            row, col = divmod(idx, cols)
            x1, y1 = col * cell_width, row * cell_height
            x2, y2 = x1 + cell_width, y1 + cell_height
            rect_id = self.canvas.create_rectangle(
                x1, y1, x2, y2, fill=self.NEUTRAL_COLOR, outline=self.BG_COLOR, width=1
            )
            self.cell_rects.append(rect_id)

    def _update_grid(self, candidate, target):
        """Update grid colors based on matches"""
        for idx in range(len(candidate)):
            if idx < len(self.cell_rects):
                color = (
                    self.MATCH_COLOR
                    if candidate[idx] == target[idx]
                    else self.NEUTRAL_COLOR
                )
                self.canvas.itemconfig(self.cell_rects[idx], fill=color)

    def _start_attack(self):
        """Start the Tabu Search attack"""
        try:
            N = int(self.n_var.get())
            keystream_length = int(self.keystream_length_var.get())
            max_iterations = int(self.max_iter_var.get())

            self.target_state, target_keystream = generate_challenge(
                N, keystream_length
            )
            self.cracker = TabuCracker(target_keystream, N)

            self._draw_grid(N)
            self.swaps_label.config(text=str(self.cracker.swaps_per_iteration))
            self.running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)

            self.cracker.run(max_iterations=max_iterations, callback=self._on_update)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start attack: {str(e)}")

    def _stop_attack(self):
        """Stop the attack"""
        if self.cracker:
            self.cracker.stop()
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def _on_update(self, stats):
        """Callback from cracker thread"""
        self.update_queue.put(stats)

    def _start_update_polling(self):
        """Poll update queue and update UI"""

        def _poll():
            try:
                while not self.update_queue.empty():
                    stats = self.update_queue.get_nowait()
                    self._update_ui(stats)
            except queue.Empty:
                pass
            finally:
                self.after(100, _poll)

        _poll()

    def _update_ui(self, stats):
        """Update UI with statistics"""
        self.iter_label.config(text=str(stats["iteration"]))
        keystream_length = len(self.cracker.target_keystream)

        current_pct = (stats["current_fitness"] / keystream_length) * 100
        self.fitness_label.config(
            text=f"{stats['current_fitness']} / {keystream_length} ({current_pct:.1f}%)"
        )

        best_pct = (stats["best_fitness"] / keystream_length) * 100
        self.best_fitness_label.config(
            text=f"{stats['best_fitness']} / {keystream_length} ({best_pct:.1f}%)"
        )

        self.tabu_label.config(text=str(stats["tabu_size"]))

        if stats["iteration"] % 10 == 0:
            self._update_grid(stats["best_candidate"], self.target_state)

        if stats["best_fitness"] == keystream_length:
            self._stop_attack()
            self._update_grid(stats["best_candidate"], self.target_state)
            messagebox.showinfo(
                "Success!", f"Perfect match found in {stats['iteration']} iterations!"
            )
        elif not self.cracker.running and self.running:
            self._stop_attack()
