import tkinter as tk
from tkinter import ttk
import queue
import math
import logging
from tabu_search.tabu_logic import generate_rc4_plus_keystream, TabuCracker
from utils.utils import show_help_text

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

        # NEW: Memory tracking for orange cells
        self.memory_correct = set()  # Set of indices that were correct at some point
        self.memory_correct_keystream = set()  # NEW: Memory for keystream bytes

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

        # Title with Help button
        title_frame = tk.Frame(left_frame, bg=self.bg_color)
        title_frame.pack(fill="x", pady=(0, 20))

        title = tk.Label(
            title_frame,
            text="Ataque Tabu Search",
            font=("Arial", 14, "bold"),
            bg=self.bg_color,
        )
        title.pack(side="left")

        # NEW: Help button
        help_button = tk.Button(
            title_frame,
            text="?",
            command=self._show_help,
            bg="#2196F3",
            fg="white",
            font=("Arial", 12, "bold"),
            width=2,
            height=1,
            cursor="hand2",
        )
        help_button.pack(side="right")

        # Configuration section
        config_frame = tk.LabelFrame(
            left_frame,
            text="Configuración",
            bg=self.bg_color,
            font=("Arial", 10, "bold"),
        )
        config_frame.pack(fill="x", pady=(0, 10))

        # N Size
        tk.Label(config_frame, text="Tamaño N:", bg=self.bg_color).pack(
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
        tk.Label(config_frame, text="Longitud Keystream:", bg=self.bg_color).pack(
            anchor="w", padx=5
        )
        self.keystream_length_var = tk.StringVar(value="32")
        keystream_entry = tk.Entry(
            config_frame, textvariable=self.keystream_length_var, width=18
        )
        keystream_entry.pack(padx=5, pady=(0, 5))

        # Max Iterations
        tk.Label(config_frame, text="Máx. Iteraciones:", bg=self.bg_color).pack(
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
            text="Iniciar Ataque",
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
            text="Detener",
            command=self._stop_attack,
            bg="#f44336",
            fg="white",
            font=("Arial", 12, "bold"),
            height=2,
            state="disabled",
            cursor="hand2",
        )
        self.stop_button.pack(fill="x", pady=(0, 10))

        # NEW: Reset button
        self.reset_button = tk.Button(
            left_frame,
            text="Reiniciar",
            command=self._reset_attack,
            bg="#FF9800",
            fg="white",
            font=("Arial", 12, "bold"),
            height=2,
            cursor="hand2",
        )
        self.reset_button.pack(fill="x", pady=(0, 20))

        # Status section
        status_frame = tk.LabelFrame(
            left_frame, text="Estado", bg=self.bg_color, font=("Arial", 10, "bold")
        )
        status_frame.pack(fill="x", pady=(0, 10))

        self.iteration_label = tk.Label(
            status_frame, text="Iteración: 0", bg=self.bg_color, font=("Arial", 10)
        )
        self.iteration_label.pack(anchor="w", padx=5, pady=2)

        self.fitness_label = tk.Label(
            status_frame, text="Fitness: 0/0", bg=self.bg_color, font=("Arial", 10)
        )
        self.fitness_label.pack(anchor="w", padx=5, pady=2)

        self.best_fitness_label = tk.Label(
            status_frame,
            text="Mejor Fitness: 0/0",
            bg=self.bg_color,
            font=("Arial", 10),
        )
        self.best_fitness_label.pack(anchor="w", padx=5, pady=2)

        self.tabu_size_label = tk.Label(
            status_frame, text="Tamaño Tabu: 0", bg=self.bg_color, font=("Arial", 10)
        )
        self.tabu_size_label.pack(anchor="w", padx=5, pady=(2, 5))

        # NEW: Success message label
        self.success_label = tk.Label(
            left_frame,
            text="",
            bg=self.bg_color,
            font=("Arial", 12, "bold"),
            fg="green",
            wraplength=230,
        )
        self.success_label.pack(fill="x", pady=(10, 0))

    def _create_right_panel(self):
        """Create right visualization panel"""
        right_frame = tk.Frame(self, bg=self.bg_color)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Configure grid for zones
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
        sbox_frame.grid_rowconfigure(2, weight=0)  # NEW: Legend row
        sbox_frame.grid_columnconfigure(0, weight=1)
        sbox_frame.grid_columnconfigure(1, weight=1)

        # Target S-Box (Left)
        target_label = tk.Label(
            sbox_frame,
            text="S-Box Objetivo (Secreto)",
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
            text="S-Box Candidato (Algoritmo)",
            font=("Arial", 11, "bold"),
            bg=self.bg_color,
        )
        candidate_label.grid(row=0, column=1, pady=(0, 5))

        self.candidate_canvas = tk.Canvas(
            sbox_frame, bg="white", highlightthickness=1, highlightbackground="gray"
        )
        self.candidate_canvas.grid(row=1, column=1, sticky="nsew", padx=(5, 0))

        # NEW: Color Legend
        self._create_color_legend(sbox_frame)

    def _create_color_legend(self, parent):
        """NEW: Create color legend for S-Box visualization"""
        legend_frame = tk.Frame(parent, bg=self.bg_color)
        legend_frame.grid(row=2, column=0, columnspan=2, pady=(5, 0))

        tk.Label(
            legend_frame,
            text="Leyenda:",
            font=("Arial", 9, "bold"),
            bg=self.bg_color,
        ).pack(side="left", padx=(0, 10))

        # Green - Correct
        green_box = tk.Canvas(
            legend_frame, width=20, height=20, bg="lightgreen", highlightthickness=1
        )
        green_box.pack(side="left", padx=2)
        tk.Label(
            legend_frame, text="Correcto", font=("Arial", 9), bg=self.bg_color
        ).pack(side="left", padx=(2, 10))

        # Orange - Was Correct
        orange_box = tk.Canvas(
            legend_frame, width=20, height=20, bg="orange", highlightthickness=1
        )
        orange_box.pack(side="left", padx=2)
        tk.Label(
            legend_frame, text="Fue Correcto", font=("Arial", 9), bg=self.bg_color
        ).pack(side="left", padx=(2, 10))

        # Red - Incorrect
        red_box = tk.Canvas(
            legend_frame, width=20, height=20, bg="lightcoral", highlightthickness=1
        )
        red_box.pack(side="left", padx=2)
        tk.Label(
            legend_frame, text="Incorrecto", font=("Arial", 9), bg=self.bg_color
        ).pack(side="left", padx=(2, 10))

        # Yellow border - Current Swap
        yellow_box = tk.Canvas(
            legend_frame,
            width=20,
            height=20,
            bg="white",
            highlightthickness=3,
            highlightbackground="gold",
        )
        yellow_box.pack(side="left", padx=2)
        tk.Label(
            legend_frame, text="Intercambio Actual", font=("Arial", 9), bg=self.bg_color
        ).pack(side="left")

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
        """MODIFIED: Create Keystream comparison zone with 3 rows - ALL with Canvas"""
        keystream_frame = tk.LabelFrame(
            parent,
            text="Comparación de Keystream",
            bg=self.bg_color,
            font=("Arial", 10, "bold"),
        )
        keystream_frame.grid(row=2, column=0, sticky="ew")

        # Target keystream - CHANGED to Canvas
        target_ks_frame = tk.Frame(keystream_frame, bg=self.bg_color)
        target_ks_frame.pack(fill="x", padx=5, pady=(5, 2))

        tk.Label(
            target_ks_frame,
            text="Salida Objetivo:",
            font=("Arial", 9, "bold"),
            bg=self.bg_color,
            width=15,
            anchor="w",
        ).pack(side="left")

        self.target_ks_canvas = tk.Canvas(
            target_ks_frame,
            height=25,
            bg="white",
            highlightthickness=1,
            highlightbackground="gray",
        )
        self.target_ks_canvas.pack(side="left", fill="x", expand=True)

        # Current keystream
        current_ks_frame = tk.Frame(keystream_frame, bg=self.bg_color)
        current_ks_frame.pack(fill="x", padx=5, pady=2)

        tk.Label(
            current_ks_frame,
            text="Salida Actual:",
            font=("Arial", 9, "bold"),
            bg=self.bg_color,
            width=15,
            anchor="w",
        ).pack(side="left")

        self.current_ks_canvas = tk.Canvas(
            current_ks_frame,
            height=25,
            bg="white",
            highlightthickness=1,
            highlightbackground="gray",
        )
        self.current_ks_canvas.pack(side="left", fill="x", expand=True)

        # Best keystream
        best_ks_frame = tk.Frame(keystream_frame, bg=self.bg_color)
        best_ks_frame.pack(fill="x", padx=5, pady=(2, 5))

        tk.Label(
            best_ks_frame,
            text="Mejor Salida:",
            font=("Arial", 9, "bold"),
            bg=self.bg_color,
            width=15,
            anchor="w",
        ).pack(side="left")

        self.best_ks_canvas = tk.Canvas(
            best_ks_frame,
            height=25,
            bg="white",
            highlightthickness=1,
            highlightbackground="gray",
        )
        self.best_ks_canvas.pack(side="left", fill="x", expand=True)

    def _draw_sbox(self, canvas, sbox_array, target_sbox=None, current_swap=None):
        """MODIFIED: Draw S-Box with colored borders for swap highlighting"""
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

            # Determine cell color and border
            is_swap_cell = current_swap and idx in current_swap

            if target_sbox is not None:
                # Candidate S-Box: color based on match and memory
                is_currently_correct = sbox_array[idx] == target_sbox[idx]
                was_correct = idx in self.memory_correct

                # Determine fill color (background)
                if is_currently_correct:
                    fill_color = "lightgreen"
                    self.memory_correct.add(idx)  # Add to memory
                elif was_correct:
                    fill_color = "orange"  # Was correct before
                else:
                    fill_color = "lightcoral"

                # Determine border (outline)
                if is_swap_cell:
                    outline_color = "gold"  # Yellow/gold border for swap
                    outline_width = 4
                else:
                    outline_color = "gray"
                    outline_width = 1
            else:
                # Target S-Box: standard color
                fill_color = "white"
                outline_color = "gray"
                outline_width = 1

            # Draw cell
            canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill=fill_color,
                outline=outline_color,
                width=outline_width,
            )

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

    def _draw_keystream_row(
        self, canvas, target_ks, actual_ks, use_colors=True, use_memory=False
    ):
        """MODIFIED: Draw a single keystream comparison row with optional coloring and memory"""
        canvas.delete("all")

        if target_ks is None or actual_ks is None:
            return

        # Limit display to first 20 bytes
        display_length = min(20, len(target_ks))

        # Get canvas dimensions
        canvas.update_idletasks()
        canvas_width = canvas.winfo_width()
        if canvas_width < 10:
            canvas_width = 600

        cell_width = canvas_width / display_length

        for i in range(display_length):
            x1 = i * cell_width
            x2 = x1 + cell_width

            # Determine color
            if not use_colors:
                # Current output: no colors
                fill_color = "white"
            elif use_memory:
                # Best output: with memory system
                is_currently_correct = actual_ks[i] == target_ks[i]
                was_correct = i in self.memory_correct_keystream

                if is_currently_correct:
                    fill_color = "lightgreen"
                    self.memory_correct_keystream.add(i)  # Add to memory
                elif was_correct:
                    fill_color = "orange"  # Was correct before
                else:
                    fill_color = "lightcoral"
            else:
                # Simple coloring (no memory)
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

    def _draw_keystream_comparison(self, target_ks, current_ks, best_ks):
        """MODIFIED: Draw all three keystream rows - Target also with boxes"""
        # Draw target keystream WITH boxes (no colors)
        self._draw_keystream_row(
            self.target_ks_canvas,
            target_ks,
            target_ks,  # Compare with itself to show all white
            use_colors=False,
            use_memory=False,
        )

        # Draw current keystream WITHOUT colors
        self._draw_keystream_row(
            self.current_ks_canvas,
            target_ks,
            current_ks,
            use_colors=False,
            use_memory=False,
        )

        # Draw best keystream WITH colors and memory
        self._draw_keystream_row(
            self.best_ks_canvas, target_ks, best_ks, use_colors=True, use_memory=True
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
                # NEW: Show error in GUI instead of messagebox
                self.success_label.config(
                    text="ERROR: La longitud del keystream debe estar entre 1 y 256", fg="red"
                )
                return
            if max_iterations < 1:
                self.success_label.config(
                    text="ERROR: Las iteraciones máximas deben ser positivas", fg="red"
                )
                return

            logger.info(
                f"Starting attack: N={N}, length={keystream_length}, max_iter={max_iterations}"
            )

            # Clear previous state
            self.memory_correct.clear()
            self.memory_correct_keystream.clear()
            self.success_label.config(text="Buscando...", fg="blue")

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

            # MODIFIED: Use delay=0.05 for smooth visualization
            self.cracker.run(
                max_iterations=max_iterations, callback=callback, delay=0.05
            )

            logger.info("Attack started successfully")

        except Exception as e:
            logger.error(f"Failed to start attack: {e}", exc_info=True)
            # NEW: Show error in GUI
            self.success_label.config(text=f"ERROR: {str(e)}", fg="red")
            self._stop_attack()

    def _stop_attack(self):
        """Stop the running attack"""
        self.is_running = False

        if self.cracker:
            self.cracker.stop()

        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.success_label.config(text="Ataque detenido", fg="red")

        logger.info("Attack stopped")

    def _reset_attack(self):
        """NEW: Reset the attack to initial state"""
        logger.info("Resetting attack")

        # Stop if running
        if self.is_running:
            self._stop_attack()

        # Clear all state
        self.cracker = None
        self.target_state = None
        self.target_keystream = None
        self.memory_correct.clear()
        self.memory_correct_keystream.clear()

        # Clear queue
        while not self.update_queue.empty():
            try:
                self.update_queue.get_nowait()
            except queue.Empty:
                break

        # Reset UI elements
        self.iteration_label.config(text="Iteración: 0")
        self.fitness_label.config(text="Fitness: 0/0")
        self.best_fitness_label.config(text="Mejor Fitness: 0/0")
        self.tabu_size_label.config(text="Tamaño Tabu: 0")
        self.success_label.config(text="")

        # Clear visualizations - MODIFIED to include target_ks_canvas
        self.target_canvas.delete("all")
        self.candidate_canvas.delete("all")
        self.target_ks_canvas.delete("all")  # NEW
        self.current_ks_canvas.delete("all")
        self.best_ks_canvas.delete("all")
        self.tabu_listbox.delete(0, tk.END)

        # Enable start button
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

        logger.info("Attack reset completed")

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
            self.iteration_label.config(text=f"Iteración: {stats['iteration']}")

            keystream_length = len(stats["target_keystream"])
            self.fitness_label.config(
                text=f"Fitness: {stats['current_fitness']}/{keystream_length}"
            )
            self.best_fitness_label.config(
                text=f"Mejor Fitness: {stats['best_fitness']}/{keystream_length}"
            )
            self.tabu_size_label.config(text=f"Tamaño Tabu: {stats['tabu_size']}")

            # Update S-Box visualizations
            # MODIFIED: Use display_candidate (PRE-swap state) for visualization with yellow border
            self._draw_sbox(
                self.candidate_canvas,
                stats.get(
                    "display_candidate", stats["current_candidate"]
                ),  # Use display_candidate if available
                target_sbox=stats["target_state"],
                current_swap=stats.get("current_swap"),
            )

            # Update keystream comparison (3 rows)
            self._draw_keystream_comparison(
                stats["target_keystream"],
                stats["predicted_keystream"],
                stats.get("best_predicted_keystream", stats["predicted_keystream"]),
            )

            # Update tabu list
            if self.cracker:
                self._update_tabu_list(self.cracker.tabu_deque)

            # Check for completion
            if stats["best_fitness"] == keystream_length:
                self._stop_attack()
                # NEW: Show success in GUI instead of messagebox
                self.success_label.config(
                    text=f"¡ÉXITO! SOLUCIÓN ENCONTRADA\nEn {stats['iteration']} iteraciones",
                    fg="green",
                    font=("Arial", 14, "bold"),
                )

        except Exception as e:
            logger.error(f"Error updating UI: {e}", exc_info=True)

    def _show_help(self):
        """NEW: Show help window with mountain metaphor"""
        help_window = tk.Toplevel(self.parent)
        help_window.title("Ayuda - Búsqueda Tabú")
        help_window.geometry("700x600")
        help_window.configure(bg=self.bg_color)

        # Make it modal
        help_window.transient(self.parent)
        help_window.grab_set()

        # Title
        title = tk.Label(
            help_window,
            text="Guía de la Herramienta",
            font=("Arial", 16, "bold"),
            bg=self.bg_color,
        )
        title.pack(pady=(20, 10))

        # Main text frame with scrollbar
        text_frame = tk.Frame(help_window, bg="white", relief="sunken", borderwidth=1)
        text_frame.pack(fill="both", expand=True, padx=20, pady=10)
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        # Text widget for formatted content
        help_text_widget = tk.Text(
            text_frame,
            wrap="word",
            bg="white",
            font=("Arial", 11),
            padx=15,
            pady=15,
            borderwidth=0,
            highlightthickness=0,
        )
        help_text_widget.grid(row=0, column=0, sticky="nsew")

        # Scrollbar
        scrollbar = ttk.Scrollbar(text_frame, command=help_text_widget.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        help_text_widget.config(yscrollcommand=scrollbar.set)

        # Define text styles (tags)
        help_text_widget.tag_configure("h1", font=("Arial", 12, "bold"), spacing3=10)
        help_text_widget.tag_configure("h2", font=("Arial", 11, "bold"), spacing3=5)
        help_text_widget.tag_configure("bold", font=("Arial", 11, "bold"))
        help_text_widget.tag_configure("bullet", lmargin1=20, lmargin2=20)
        help_text_widget.tag_configure(
            "code", font=("Courier", 10), background="#f0f0f0"
        )
        help_text_widget.tag_configure("success", foreground="green")
        help_text_widget.tag_configure("error", foreground="red")
        help_text_widget.tag_configure("antes_success", foreground="orange")
        help_text_widget.tag_configure("info", foreground="blue")
        # Get and insert formatted text
        help_text = show_help_text()
        for line in help_text.split("\n"):
            if line.startswith("Ayuda:"):
                help_text_widget.insert(tk.END, line + "\n\n", "h1")
            elif line and line[0].isdigit() and "." in line:
                help_text_widget.insert(tk.END, line + "\n", "h2")
            elif line.strip().startswith("-"):
                clean_line = line.strip()[1:].strip()
                parts = clean_line.split(":", 1)

                if len(parts) == 2:
                    help_text_widget.insert(tk.END, "• ", "bullet")

                    # Lógica para elegir el icono y color según el texto
                    key_text = parts[0]
                    icon = ""
                    style = ("bullet", "bold")  # Estilo por defecto

                    if "Incorrecto" in key_text:
                        icon = "✖ "
                        style = ("bullet", "bold", "error")
                    elif "Fue Correcto" in key_text:
                        icon = "⚠️ "
                        style = ("bullet", "bold", "antes_success")
                    elif "Correcto" in key_text:
                        icon = "✔ "
                        style = ("bullet", "bold", "success")
                    elif "Intercambio" in key_text:
                        icon = "⇄ "
                        style = ("bullet", "bold", "info")

                    # Insertar con el icono y color seleccionado
                    help_text_widget.insert(tk.END, f"{icon}{key_text}:", style)
                    help_text_widget.insert(tk.END, f"{parts[1]}\n", "bullet")
                else:
                    help_text_widget.insert(tk.END, f"• {clean_line}\n", "bullet")
            else:
                help_text_widget.insert(tk.END, line + "\n")

        # Disable editing
        help_text_widget.config(state="disabled")

        # Close button
        close_button = tk.Button(
            help_window,
            text="Cerrar",
            command=help_window.destroy,
            bg="#2196F3",
            fg="white",
            font=("Arial", 11, "bold"),
            cursor="hand2",
            padx=20,
            pady=5,
        )
        close_button.pack(pady=(0, 20))


def main():
    """Main entry point"""
    root = tk.Tk()
    root.title("Ataque Tabu Search RC4+ - Herramienta Educativa")
    root.geometry("1400x900")

    # Create main frame
    app = TabuAttackGUI(root)
    app.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
