import tkinter as tk
from tkinter import ttk, messagebox
import queue
import math
import logging
from tabu_logic import generate_rc4_plus_keystream, TabuCracker

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TabuAttackGUI(tk.Frame):
    """
    Educational GUI for Tabu Search RC4+ State Recovery Attack
    """

    def __init__(self, parent):
        # Use a cross-platform compatible background color
        bg_color = "#f0f0f0"  # Light gray, similar to SystemButtonFace
        super().__init__(parent, bg=bg_color)
        self.parent = parent
        self.bg_color = bg_color

        # Attack state
        self.cracker = None
        self.target_state = None
        self.target_keystream = None
        self.update_queue = queue.Queue()
        self.is_running = False

        # UI update rate (ms)
        self.update_interval = 100

        # Build the interface
        self._build_ui()

        # Start UI update loop
        self._schedule_ui_update()

        logger.info("TabuSearchFrame initialized")

    def _build_ui(self):
        """Build the complete UI layout"""
        # Configure grid weights for responsive layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)  # Left panel (fixed)
        self.grid_columnconfigure(1, weight=1)  # Right panel (expandable)

        # Create left and right panels
        self._create_left_panel()
        self._create_right_panel()

    def _create_left_panel(self):
        """Create left control panel"""
        left_frame = tk.Frame(self, bg=self.bg_color, width=250)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        left_frame.grid_propagate(False)

        # Title
        title = tk.Label(
            left_frame,
            text="Tabu Search Attack",
            font=("Arial", 14, "bold"),
            bg=self.bg_color,
        )
        title.pack(pady=(0, 20))

        # Configuration section
        config_frame = tk.LabelFrame(
            left_frame,
            text="Configuration",
            bg=self.bg_color,
            font=("Arial", 10, "bold"),
        )
        config_frame.pack(fill="x", pady=(0, 10))

        # N Size
        tk.Label(config_frame, text="N Size:", bg=self.bg_color).pack(
            anchor="w", padx=5, pady=(5, 0)
        )
        self.n_size_var = tk.StringVar(value="256")
        n_combo = ttk.Combobox(
            config_frame,
            textvariable=self.n_size_var,
            values=["64", "128", "256"],
            state="readonly",
            width=15,
        )
        n_combo.pack(padx=5, pady=(0, 5))

        # Keystream Length
        tk.Label(config_frame, text="Keystream Length:", bg=self.bg_color).pack(
            anchor="w", padx=5
        )
        self.keystream_length_var = tk.StringVar(value="32")
        keystream_entry = tk.Entry(
            config_frame, textvariable=self.keystream_length_var, width=18
        )
        keystream_entry.pack(padx=5, pady=(0, 5))

        # Max Iterations
        tk.Label(config_frame, text="Max Iterations:", bg=self.bg_color).pack(
            anchor="w", padx=5
        )
        self.max_iterations_var = tk.StringVar(value="10000")
        iterations_entry = tk.Entry(
            config_frame, textvariable=self.max_iterations_var, width=18
        )
        iterations_entry.pack(padx=5, pady=(0, 10))

        # Control buttons
        self.start_button = tk.Button(
            left_frame,
            text="Start Attack",
            command=self._start_attack,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            height=2,
            cursor="hand2",
        )
        self.start_button.pack(fill="x", pady=(0, 10))

        self.stop_button = tk.Button(
            left_frame,
            text="Stop",
            command=self._stop_attack,
            bg="#f44336",
            fg="white",
            font=("Arial", 12, "bold"),
            height=2,
            state="disabled",
            cursor="hand2",
        )
        self.stop_button.pack(fill="x", pady=(0, 20))

        # Status section
        status_frame = tk.LabelFrame(
            left_frame, text="Status", bg=self.bg_color, font=("Arial", 10, "bold")
        )
        status_frame.pack(fill="x", pady=(0, 10))

        self.iteration_label = tk.Label(
            status_frame, text="Iteration: 0", bg=self.bg_color, font=("Arial", 10)
        )
        self.iteration_label.pack(anchor="w", padx=5, pady=2)

        self.fitness_label = tk.Label(
            status_frame, text="Fitness: 0/0", bg=self.bg_color, font=("Arial", 10)
        )
        self.fitness_label.pack(anchor="w", padx=5, pady=2)

        self.best_fitness_label = tk.Label(
            status_frame,
            text="Best Fitness: 0/0",
            bg=self.bg_color,
            font=("Arial", 10),
        )
        self.best_fitness_label.pack(anchor="w", padx=5, pady=2)

        self.tabu_size_label = tk.Label(
            status_frame, text="Tabu Size: 0", bg=self.bg_color, font=("Arial", 10)
        )
        self.tabu_size_label.pack(anchor="w", padx=5, pady=(2, 5))

    def _create_right_panel(self):
        """Create right visualization panel"""
        right_frame = tk.Frame(self, bg=self.bg_color)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Configure grid for three zones
        right_frame.grid_rowconfigure(0, weight=3)  # S-Boxes (larger)
        right_frame.grid_rowconfigure(1, weight=1)  # Tabu List
        right_frame.grid_rowconfigure(2, weight=0)  # Keystream (fixed)
        right_frame.grid_columnconfigure(0, weight=1)

        # Zone 1: S-Boxes
        self._create_sbox_zone(right_frame)

        # Zone 2: Tabu List
        self._create_tabu_zone(right_frame)

        # Zone 3: Keystream
        self._create_keystream_zone(right_frame)

    def _create_sbox_zone(self, parent):
        """Create S-Box visualization zone"""
        sbox_frame = tk.Frame(parent, bg=self.bg_color)
        sbox_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        # Configure grid for two canvases side by side
        sbox_frame.grid_rowconfigure(0, weight=0)  # Title row
        sbox_frame.grid_rowconfigure(1, weight=1)  # Canvas row
        sbox_frame.grid_columnconfigure(0, weight=1)
        sbox_frame.grid_columnconfigure(1, weight=1)

        # Target S-Box (Left)
        target_label = tk.Label(
            sbox_frame,
            text="Target S-Box (Objetivo Secreto)",
            font=("Arial", 11, "bold"),
            bg=self.bg_color,
        )
        target_label.grid(row=0, column=0, pady=(0, 5))

        self.target_canvas = tk.Canvas(
            sbox_frame, bg="white", highlightthickness=1, highlightbackground="gray"
        )
        self.target_canvas.grid(row=1, column=0, sticky="nsew", padx=(0, 5))

        # Candidate S-Box (Right)
        candidate_label = tk.Label(
            sbox_frame,
            text="Candidate S-Box (Algoritmo)",
            font=("Arial", 11, "bold"),
            bg=self.bg_color,
        )
        candidate_label.grid(row=0, column=1, pady=(0, 5))

        self.candidate_canvas = tk.Canvas(
            sbox_frame, bg="white", highlightthickness=1, highlightbackground="gray"
        )
        self.candidate_canvas.grid(row=1, column=1, sticky="nsew", padx=(5, 0))

    def _create_tabu_zone(self, parent):
        """Create Tabu List visualization zone"""
        tabu_frame = tk.LabelFrame(
            parent,
            text="Tabu List (Movimientos Prohibidos)",
            bg=self.bg_color,
            font=("Arial", 10, "bold"),
        )
        tabu_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))

        # Configure grid
        tabu_frame.grid_rowconfigure(0, weight=1)
        tabu_frame.grid_columnconfigure(0, weight=1)
        tabu_frame.grid_columnconfigure(1, weight=0)

        # Listbox with scrollbar
        self.tabu_listbox = tk.Listbox(tabu_frame, font=("Courier", 9), bg="white")
        self.tabu_listbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        scrollbar = tk.Scrollbar(tabu_frame, command=self.tabu_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=5, padx=(0, 5))
        self.tabu_listbox.config(yscrollcommand=scrollbar.set)

    def _create_keystream_zone(self, parent):
        """Create Keystream comparison zone"""
        keystream_frame = tk.LabelFrame(
            parent,
            text="Keystream Comparison",
            bg=self.bg_color,
            font=("Arial", 10, "bold"),
        )
        keystream_frame.grid(row=2, column=0, sticky="ew")

        # Target keystream
        target_ks_frame = tk.Frame(keystream_frame, bg=self.bg_color)
        target_ks_frame.pack(fill="x", padx=5, pady=(5, 2))

        tk.Label(
            target_ks_frame,
            text="Target Output:",
            font=("Arial", 9, "bold"),
            bg=self.bg_color,
            width=15,
            anchor="w",
        ).pack(side="left")

        self.target_ks_label = tk.Label(
            target_ks_frame,
            text="",
            font=("Courier", 9),
            bg="white",
            anchor="w",
            relief="sunken",
        )
        self.target_ks_label.pack(side="left", fill="x", expand=True)

        # Actual keystream
        actual_ks_frame = tk.Frame(keystream_frame, bg=self.bg_color)
        actual_ks_frame.pack(fill="x", padx=5, pady=(2, 5))

        tk.Label(
            actual_ks_frame,
            text="Actual Output:",
            font=("Arial", 9, "bold"),
            bg=self.bg_color,
            width=15,
            anchor="w",
        ).pack(side="left")

        self.actual_ks_canvas = tk.Canvas(
            actual_ks_frame,
            height=25,
            bg="white",
            highlightthickness=1,
            highlightbackground="gray",
        )
        self.actual_ks_canvas.pack(side="left", fill="x", expand=True)

    def _draw_sbox(self, canvas, sbox_array, target_sbox=None):
        """Draw S-Box as a grid on canvas"""
        canvas.delete("all")

        if sbox_array is None:
            return

        N = len(sbox_array)

        # Calculate grid dimensions
        grid_size = int(math.sqrt(N))
        if grid_size * grid_size < N:
            grid_size += 1

        # Get canvas dimensions
        canvas.update_idletasks()
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()

        if canvas_width < 10 or canvas_height < 10:
            canvas_width = 400
            canvas_height = 400

        # Calculate cell size
        cell_width = canvas_width / grid_size
        cell_height = canvas_height / grid_size

        # Draw grid
        for idx in range(N):
            row = idx // grid_size
            col = idx % grid_size

            x1 = col * cell_width
            y1 = row * cell_height
            x2 = x1 + cell_width
            y2 = y1 + cell_height

            # Determine cell color
            if target_sbox is not None:
                # Candidate S-Box: color based on match
                if sbox_array[idx] == target_sbox[idx]:
                    fill_color = "lightgreen"
                else:
                    fill_color = "lightcoral"
            else:
                # Target S-Box: standard color
                fill_color = "white"

            # Draw cell
            canvas.create_rectangle(x1, y1, x2, y2, fill=fill_color, outline="gray")

            # Draw value (only if cell is large enough)
            if cell_width > 20 and cell_height > 15:
                value_text = (
                    f"{sbox_array[idx]:02X}" if N <= 256 else str(sbox_array[idx])
                )
                font_size = max(6, min(10, int(cell_height / 2)))
                canvas.create_text(
                    (x1 + x2) / 2,
                    (y1 + y2) / 2,
                    text=value_text,
                    font=("Courier", font_size),
                    fill="black",
                )

    def _draw_keystream_comparison(self, target_ks, actual_ks):
        """Draw keystream comparison with color coding"""
        canvas = self.actual_ks_canvas
        canvas.delete("all")

        if target_ks is None or actual_ks is None:
            return

        # Limit display to first 20 bytes
        display_length = min(20, len(target_ks))

        # Update target label
        target_text = " ".join([f"{b:02X}" for b in target_ks[:display_length]])
        if len(target_ks) > display_length:
            target_text += "..."
        self.target_ks_label.config(text=target_text)

        # Draw actual keystream with color coding
        canvas.update_idletasks()
        canvas_width = canvas.winfo_width()
        if canvas_width < 10:
            canvas_width = 600

        cell_width = canvas_width / display_length

        for i in range(display_length):
            x1 = i * cell_width
            x2 = x1 + cell_width

            # Determine color
            if actual_ks[i] == target_ks[i]:
                fill_color = "lightgreen"
            else:
                fill_color = "lightcoral"

            # Draw cell
            canvas.create_rectangle(x1, 2, x2, 23, fill=fill_color, outline="gray")

            # Draw value
            canvas.create_text(
                (x1 + x2) / 2,
                12,
                text=f"{actual_ks[i]:02X}",
                font=("Courier", 9),
                fill="black",
            )

    def _update_tabu_list(self, tabu_deque):
        """Update tabu list display"""
        self.tabu_listbox.delete(0, tk.END)

        if tabu_deque is None or len(tabu_deque) == 0:
            return

        for move in tabu_deque:
            move_text = f"Swap({move[0]:3d}, {move[1]:3d})"
            self.tabu_listbox.insert(tk.END, move_text)

        # Auto-scroll to bottom
        self.tabu_listbox.see(tk.END)

    def _start_attack(self):
        """Start the Tabu Search attack"""
        try:
            # Get parameters
            N = int(self.n_size_var.get())
            keystream_length = int(self.keystream_length_var.get())
            max_iterations = int(self.max_iterations_var.get())

            # Validate parameters
            if keystream_length < 1 or keystream_length > 256:
                raise ValueError("Keystream length must be between 1 and 256")
            if max_iterations < 1:
                raise ValueError("Max iterations must be positive")

            logger.info(
                f"Starting attack: N={N}, length={keystream_length}, max_iter={max_iterations}"
            )

            # Generate challenge
            self.target_state, self.target_keystream = generate_rc4_plus_keystream(
                N, keystream_length
            )

            # Draw target S-Box
            self._draw_sbox(self.target_canvas, self.target_state)

            # Initialize cracker
            self.cracker = TabuCracker(
                self.target_keystream, N=N, target_state=self.target_state
            )

            # Update UI state
            self.is_running = True
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.n_size_var.set(str(N))  # Lock value

            # Start attack in background
            def callback(stats):
                self.update_queue.put(stats)

            self.cracker.run(max_iterations=max_iterations, callback=callback)

            logger.info("Attack started successfully")

        except Exception as e:
            logger.error(f"Failed to start attack: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to start attack:\n{str(e)}")
            self._stop_attack()

    def _stop_attack(self):
        """Stop the running attack"""
        self.is_running = False

        if self.cracker:
            self.cracker.stop()

        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

        logger.info("Attack stopped")

    def _schedule_ui_update(self):
        """Schedule periodic UI updates"""
        self._process_update_queue()
        self.after(self.update_interval, self._schedule_ui_update)

    def _process_update_queue(self):
        """Process all pending updates from the queue"""
        try:
            while True:
                stats = self.update_queue.get_nowait()
                self._update_ui(stats)
        except queue.Empty:
            pass

    def _update_ui(self, stats):
        """Update UI with current statistics"""
        try:
            # Update status labels
            self.iteration_label.config(text=f"Iteration: {stats['iteration']}")

            keystream_length = len(stats["target_keystream"])
            self.fitness_label.config(
                text=f"Fitness: {stats['current_fitness']}/{keystream_length}"
            )
            self.best_fitness_label.config(
                text=f"Best Fitness: {stats['best_fitness']}/{keystream_length}"
            )
            self.tabu_size_label.config(text=f"Tabu Size: {stats['tabu_size']}")

            # Update S-Box visualizations
            self._draw_sbox(
                self.candidate_canvas,
                stats["current_candidate"],
                target_sbox=stats["target_state"],
            )

            # Update keystream comparison
            self._draw_keystream_comparison(
                stats["target_keystream"], stats["predicted_keystream"]
            )

            # Update tabu list
            if self.cracker:
                self._update_tabu_list(self.cracker.tabu_deque)

            # Check for completion
            if stats["best_fitness"] == keystream_length:
                self._stop_attack()
                messagebox.showinfo(
                    "Success!", f"State recovered in {stats['iteration']} iterations!"
                )

        except Exception as e:
            logger.error(f"Error updating UI: {e}", exc_info=True)


def main():
    """Main entry point"""
    root = tk.Tk()
    root.title("RC4+ Tabu Search Attack - Educational Tool")
    root.geometry("1400x900")

    # Create main frame
    app = TabuAttackGUI(root)
    app.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
