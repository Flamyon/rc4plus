"""
Tabu Search Attack GUI - Enhanced Educational Visualization
Shows the attack process with detailed metrics and visual comparisons
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import logging

from tabu_logic import TabuCracker, generate_rc4_plus_keystream

logger = logging.getLogger(__name__)


class TabuAttackGUI:
    """Enhanced GUI for Tabu Search State Recovery Attack"""

    def __init__(self, root):
        self.root = root
        self.root.title("RC4+ Tabu Search State Recovery Attack - Educational Mode")
        self.root.geometry("1400x900")

        # Attack state
        self.cracker = None
        self.target_state = None
        self.target_keystream = None
        self.is_running = False

        # Visualization data
        self.fitness_history = []
        self.hamming_distance_history = []
        self.byte_matches_history = []

        self._create_widgets()
        logger.info("Tabu Attack GUI initialized")

    def _create_widgets(self):
        """Create all GUI widgets with educational layout"""

        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Title section
        title_label = ttk.Label(
            main_frame,
            text="RC4+ State Recovery using Tabu Search",
            font=("Arial", 16, "bold"),
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))

        # Left column: Configuration and Control
        self._create_control_panel(main_frame)

        # Middle column: Metrics and Progress
        self._create_metrics_panel(main_frame)

        # Right column: Visualizations
        self._create_visualization_panel(main_frame)

    def _create_control_panel(self, parent):
        """Create configuration and control panel"""
        control_frame = ttk.LabelFrame(
            parent, text="Attack Configuration", padding="10"
        )
        control_frame.grid(
            row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5)
        )

        row = 0

        # N-box size selection
        ttk.Label(control_frame, text="S-box Size (N):").grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        self.n_var = tk.IntVar(value=64)
        n_combo = ttk.Combobox(
            control_frame,
            textvariable=self.n_var,
            values=[64, 128, 256],
            state="readonly",
            width=10,
        )
        n_combo.grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1

        # Keystream length
        ttk.Label(control_frame, text="Keystream Length:").grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        self.keystream_length_var = tk.IntVar(value=32)
        ttk.Entry(control_frame, textvariable=self.keystream_length_var, width=12).grid(
            row=row, column=1, sticky=tk.W, pady=5
        )
        row += 1

        # Max iterations
        ttk.Label(control_frame, text="Max Iterations:").grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        self.max_iterations_var = tk.IntVar(value=1000)
        ttk.Entry(control_frame, textvariable=self.max_iterations_var, width=12).grid(
            row=row, column=1, sticky=tk.W, pady=5
        )
        row += 1

        ttk.Separator(control_frame, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10
        )
        row += 1

        # Control buttons
        self.generate_btn = ttk.Button(
            control_frame, text="Generate Challenge", command=self._generate_challenge
        )
        self.generate_btn.grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5
        )
        row += 1

        self.start_btn = ttk.Button(
            control_frame,
            text="Start Attack",
            command=self._start_attack,
            state=tk.DISABLED,
        )
        self.start_btn.grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5
        )
        row += 1

        self.stop_btn = ttk.Button(
            control_frame,
            text="Stop Attack",
            command=self._stop_attack,
            state=tk.DISABLED,
        )
        self.stop_btn.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        row += 1

        self.reset_btn = ttk.Button(control_frame, text="Reset", command=self._reset)
        self.reset_btn.grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5
        )
        row += 1

        ttk.Separator(control_frame, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10
        )
        row += 1

        # Algorithm explanation
        explanation_text = (
            "Tabu Search Configuration (Z2):\n\n"
            "• Neighborhood: 50% of all swaps\n"
            "• Tabu Horizon: N(N-1)/4\n"
            "• Fitness: Byte matches\n"
            "• Aspiration: Accept if better\n"
            "  than best found\n\n"
            "The algorithm explores S-box\n"
            "permutations to match the\n"
            "target keystream."
        )
        explanation_label = ttk.Label(
            control_frame, text=explanation_text, justify=tk.LEFT, font=("Arial", 9)
        )
        explanation_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)

    def _create_metrics_panel(self, parent):
        """Create metrics and progress panel"""
        metrics_frame = ttk.LabelFrame(parent, text="Attack Metrics", padding="10")
        metrics_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)

        row = 0

        # Current iteration
        ttk.Label(metrics_frame, text="Iteration:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        self.iteration_label = ttk.Label(metrics_frame, text="0")
        self.iteration_label.grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1

        # Current fitness
        ttk.Label(
            metrics_frame, text="Current Fitness:", font=("Arial", 10, "bold")
        ).grid(row=row, column=0, sticky=tk.W, pady=5)
        self.current_fitness_label = ttk.Label(metrics_frame, text="0 / 0 (0.00%)")
        self.current_fitness_label.grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1

        # Best fitness
        ttk.Label(metrics_frame, text="Best Fitness:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        self.best_fitness_label = ttk.Label(
            metrics_frame, text="0 / 0 (0.00%)", foreground="blue"
        )
        self.best_fitness_label.grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1

        # Hamming distance to target
        ttk.Label(
            metrics_frame, text="Hamming Distance:", font=("Arial", 10, "bold")
        ).grid(row=row, column=0, sticky=tk.W, pady=5)
        self.hamming_label = ttk.Label(metrics_frame, text="N/A")
        self.hamming_label.grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1

        # Tabu list size
        ttk.Label(
            metrics_frame, text="Tabu List Size:", font=("Arial", 10, "bold")
        ).grid(row=row, column=0, sticky=tk.W, pady=5)
        self.tabu_size_label = ttk.Label(metrics_frame, text="0")
        self.tabu_size_label.grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1

        ttk.Separator(metrics_frame, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10
        )
        row += 1

        # Progress visualization
        ttk.Label(
            metrics_frame, text="Attack Progress:", font=("Arial", 10, "bold")
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1

        self.progress_bar = ttk.Progressbar(
            metrics_frame, orient=tk.HORIZONTAL, length=300, mode="determinate"
        )
        self.progress_bar.grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5
        )
        row += 1

        ttk.Separator(metrics_frame, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10
        )
        row += 1

        # Keystream comparison section
        ttk.Label(
            metrics_frame, text="Keystream Comparison:", font=("Arial", 10, "bold")
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1

        # Create a frame for keystream display
        keystream_frame = ttk.Frame(metrics_frame)
        keystream_frame.grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5
        )

        # Target keystream (scrollable)
        ttk.Label(keystream_frame, text="Target:").grid(row=0, column=0, sticky=tk.W)
        self.target_keystream_text = tk.Text(
            keystream_frame, height=3, width=40, wrap=tk.WORD, font=("Courier", 8)
        )
        self.target_keystream_text.grid(row=1, column=0, sticky=(tk.W, tk.E))
        target_scroll = ttk.Scrollbar(
            keystream_frame,
            orient=tk.VERTICAL,
            command=self.target_keystream_text.yview,
        )
        target_scroll.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.target_keystream_text["yscrollcommand"] = target_scroll.set

        # Predicted keystream (scrollable)
        ttk.Label(keystream_frame, text="Predicted:").grid(
            row=2, column=0, sticky=tk.W, pady=(10, 0)
        )
        self.predicted_keystream_text = tk.Text(
            keystream_frame, height=3, width=40, wrap=tk.WORD, font=("Courier", 8)
        )
        self.predicted_keystream_text.grid(row=3, column=0, sticky=(tk.W, tk.E))
        predicted_scroll = ttk.Scrollbar(
            keystream_frame,
            orient=tk.VERTICAL,
            command=self.predicted_keystream_text.yview,
        )
        predicted_scroll.grid(row=3, column=1, sticky=(tk.N, tk.S))
        self.predicted_keystream_text["yscrollcommand"] = predicted_scroll.set

        # Status message
        row += 1
        self.status_label = ttk.Label(
            metrics_frame, text="Ready to generate challenge", foreground="green"
        )
        self.status_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=10)

    def _create_visualization_panel(self, parent):
        """Create visualization panel with plots"""
        viz_frame = ttk.LabelFrame(parent, text="Visual Analysis", padding="10")
        viz_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))

        # Create matplotlib figure with subplots
        self.fig = Figure(figsize=(6, 8), dpi=100)

        # Fitness evolution plot
        self.ax_fitness = self.fig.add_subplot(311)
        self.ax_fitness.set_title("Fitness Evolution")
        self.ax_fitness.set_xlabel("Iteration")
        self.ax_fitness.set_ylabel("Byte Matches")
        self.ax_fitness.grid(True, alpha=0.3)

        # Hamming distance plot
        self.ax_hamming = self.fig.add_subplot(312)
        self.ax_hamming.set_title("Hamming Distance to Target")
        self.ax_hamming.set_xlabel("Iteration")
        self.ax_hamming.set_ylabel("Distance")
        self.ax_hamming.grid(True, alpha=0.3)

        # S-box comparison heatmap
        self.ax_sbox = self.fig.add_subplot(313)
        self.ax_sbox.set_title("S-box Position Differences")
        self.ax_sbox.set_xlabel("Position")
        self.ax_sbox.set_ylabel("Difference")

        self.fig.tight_layout()

        # Embed in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _generate_challenge(self):
        """Generate a new challenge (target state and keystream)"""
        try:
            N = self.n_var.get()
            keystream_length = self.keystream_length_var.get()

            logger.info(f"Generating challenge: N={N}, length={keystream_length}")
            self.status_label.config(
                text="Generating challenge...", foreground="orange"
            )
            self.root.update()

            self.target_state, self.target_keystream = generate_rc4_plus_keystream(
                N, keystream_length
            )

            # Display target keystream
            self._display_keystream(self.target_keystream_text, self.target_keystream)
            self.predicted_keystream_text.delete(1.0, tk.END)

            # Reset visualization data
            self.fitness_history = []
            self.hamming_distance_history = []
            self.byte_matches_history = []

            self.status_label.config(
                text=f"Challenge generated! N={N}, Keystream length={keystream_length}",
                foreground="green",
            )
            self.start_btn.config(state=tk.NORMAL)
            logger.info("Challenge generated successfully")

        except Exception as e:
            logger.error(f"Error generating challenge: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to generate challenge:\n{e}")
            self.status_label.config(
                text="Error generating challenge", foreground="red"
            )

    def _display_keystream(self, text_widget, keystream):
        """Display keystream in text widget with formatting"""
        text_widget.delete(1.0, tk.END)
        # Format as hex: XX XX XX ...
        hex_str = " ".join(f"{byte:02X}" for byte in keystream)
        text_widget.insert(1.0, hex_str)

    def _start_attack(self):
        """Start the Tabu Search attack"""
        try:
            if self.target_keystream is None:
                messagebox.showwarning("Warning", "Please generate a challenge first!")
                return

            N = self.n_var.get()
            max_iterations = self.max_iterations_var.get()

            logger.info(f"Starting attack: N={N}, max_iterations={max_iterations}")
            self.status_label.config(text="Attack running...", foreground="blue")

            # Initialize cracker
            self.cracker = TabuCracker(
                self.target_keystream, N=N, target_state=self.target_state
            )

            # Reset histories
            self.fitness_history = []
            self.hamming_distance_history = []
            self.byte_matches_history = []

            # Update UI state
            self.is_running = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.generate_btn.config(state=tk.DISABLED)

            # Start attack in background
            self.cracker.run(
                max_iterations=max_iterations, callback=self._update_callback
            )

            logger.info("Attack started")

        except Exception as e:
            logger.error(f"Error starting attack: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to start attack:\n{e}")
            self.status_label.config(text="Error starting attack", foreground="red")

    def _stop_attack(self):
        """Stop the running attack"""
        if self.cracker:
            self.cracker.stop()
        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.generate_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Attack stopped", foreground="orange")
        logger.info("Attack stopped by user")

    def _reset(self):
        """Reset the GUI to initial state"""
        if self.is_running:
            self._stop_attack()

        self.cracker = None
        self.target_state = None
        self.target_keystream = None
        self.fitness_history = []
        self.hamming_distance_history = []
        self.byte_matches_history = []

        # Reset labels
        self.iteration_label.config(text="0")
        self.current_fitness_label.config(text="0 / 0 (0.00%)")
        self.best_fitness_label.config(text="0 / 0 (0.00%)")
        self.hamming_label.config(text="N/A")
        self.tabu_size_label.config(text="0")
        self.progress_bar["value"] = 0

        # Clear text widgets
        self.target_keystream_text.delete(1.0, tk.END)
        self.predicted_keystream_text.delete(1.0, tk.END)

        # Clear plots
        for ax in [self.ax_fitness, self.ax_hamming, self.ax_sbox]:
            ax.clear()
        self.ax_fitness.set_title("Fitness Evolution")
        self.ax_fitness.grid(True, alpha=0.3)
        self.ax_hamming.set_title("Hamming Distance to Target")
        self.ax_hamming.grid(True, alpha=0.3)
        self.ax_sbox.set_title("S-box Position Differences")
        self.canvas.draw()

        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        self.generate_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Ready to generate challenge", foreground="green")
        logger.info("GUI reset")

    def _update_callback(self, stats):
        """Callback function for attack updates"""
        try:
            self.root.after(0, lambda: self._update_ui(stats))
        except Exception as e:
            logger.error(f"Error in update callback: {e}", exc_info=True)

    def _update_ui(self, stats):
        """Update UI with attack statistics"""
        try:
            iteration = stats["iteration"]
            current_fitness = stats["current_fitness"]
            best_fitness = stats["best_fitness"]
            tabu_size = stats["tabu_size"]
            keystream_length = len(self.target_keystream)

            # Update labels
            self.iteration_label.config(text=str(iteration))

            current_pct = (current_fitness / keystream_length) * 100
            self.current_fitness_label.config(
                text=f"{current_fitness} / {keystream_length} ({current_pct:.2f}%)"
            )

            best_pct = (best_fitness / keystream_length) * 100
            self.best_fitness_label.config(
                text=f"{best_fitness} / {keystream_length} ({best_pct:.2f}%)"
            )

            self.tabu_size_label.config(text=str(tabu_size))

            # Calculate Hamming distance if target state is available
            if self.target_state is not None:
                hamming_dist = np.sum(stats["best_candidate"] != self.target_state)
                self.hamming_label.config(text=f"{hamming_dist} / {self.n_var.get()}")
                self.hamming_distance_history.append(hamming_dist)

            # Update progress bar
            max_iter = self.max_iterations_var.get()
            progress = (iteration / max_iter) * 100
            self.progress_bar["value"] = progress

            # Update histories
            self.fitness_history.append(best_fitness)
            self.byte_matches_history.append(current_fitness)

            # Update keystream display
            if "predicted_keystream" in stats:
                self._display_keystream(
                    self.predicted_keystream_text, stats["predicted_keystream"]
                )

            # Update plots every 10 iterations to reduce overhead
            if iteration % 10 == 0 or best_fitness == keystream_length:
                self._update_plots()

            # Check if attack completed
            if best_fitness == keystream_length:
                self.status_label.config(
                    text=f"✓ Attack successful! State recovered in {iteration} iterations",
                    foreground="green",
                )
                self._stop_attack()
                messagebox.showinfo(
                    "Success",
                    f"State recovered successfully!\n\n"
                    f"Iterations: {iteration}\n"
                    f"Final fitness: {best_fitness}/{keystream_length}",
                )
            elif not self.is_running:
                self.status_label.config(
                    text=f"Attack stopped at iteration {iteration}",
                    foreground="orange",
                )

        except Exception as e:
            logger.error(f"Error updating UI: {e}", exc_info=True)

    def _update_plots(self):
        """Update visualization plots"""
        try:
            # Clear previous plots
            self.ax_fitness.clear()
            self.ax_hamming.clear()
            self.ax_sbox.clear()

            # Plot fitness evolution
            if len(self.fitness_history) > 0:
                iterations = list(range(1, len(self.fitness_history) + 1))
                self.ax_fitness.plot(
                    iterations, self.fitness_history, "b-", label="Best", linewidth=2
                )
                if len(self.byte_matches_history) > 0:
                    self.ax_fitness.plot(
                        iterations,
                        self.byte_matches_history,
                        "g-",
                        label="Current",
                        alpha=0.5,
                    )
                self.ax_fitness.axhline(
                    y=len(self.target_keystream),
                    color="r",
                    linestyle="--",
                    label="Target",
                )
                self.ax_fitness.set_title("Fitness Evolution")
                self.ax_fitness.set_xlabel("Iteration")
                self.ax_fitness.set_ylabel("Byte Matches")
                self.ax_fitness.legend()
                self.ax_fitness.grid(True, alpha=0.3)

            # Plot Hamming distance
            if len(self.hamming_distance_history) > 0:
                iterations = list(range(1, len(self.hamming_distance_history) + 1))
                self.ax_hamming.plot(
                    iterations, self.hamming_distance_history, "r-", linewidth=2
                )
                self.ax_hamming.set_title("Hamming Distance to Target S-box")
                self.ax_hamming.set_xlabel("Iteration")
                self.ax_hamming.set_ylabel("Distance (positions)")
                self.ax_hamming.grid(True, alpha=0.3)

            # Plot S-box differences (bar chart of differences)
            if self.cracker and self.target_state is not None:
                state = self.cracker.get_current_state()
                best_candidate = state["best_candidate"]
                differences = np.abs(
                    best_candidate.astype(int) - self.target_state.astype(int)
                )

                # Sample points for visualization if N is large
                N = len(differences)
                if N > 64:
                    sample_indices = np.linspace(0, N - 1, 64, dtype=int)
                    differences = differences[sample_indices]
                    positions = sample_indices
                else:
                    positions = np.arange(N)

                self.ax_sbox.bar(positions, differences, color="purple", alpha=0.6)
                self.ax_sbox.set_title(f"S-box Value Differences (N={N})")
                self.ax_sbox.set_xlabel("Position")
                self.ax_sbox.set_ylabel("Absolute Difference")
                self.ax_sbox.grid(True, alpha=0.3, axis="y")

            self.fig.tight_layout()
            self.canvas.draw()

        except Exception as e:
            logger.error(f"Error updating plots: {e}", exc_info=True)


def main():
    """Main entry point for the GUI"""
    root = tk.Tk()
    TabuAttackGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
