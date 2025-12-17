"""
Visualization Module for RC4/RC4+ State
Handles drawing the S-box state on a canvas
"""

import math
import tkinter as tk


class StateVisualizer:
    """Handles visualization of the RC4 state array"""

    # Color scheme for highlighting different indices
    COLORS = {
        "i": {"fill": "lightblue", "outline": "blue", "text": "blue"},
        "j": {"fill": "lightcoral", "outline": "red", "text": "red"},
        "t": {"fill": "lightyellow", "outline": "orange", "text": "orange"},
        "t_prime": {"fill": "lightgreen", "outline": "green", "text": "green"},
        "t_double": {"fill": "lightpink", "outline": "magenta", "text": "magenta"},
        "default": {"fill": "white", "outline": "gray", "text": "black"},
    }

    def __init__(self, canvas, available_width=800, available_height=600):
        """
        Initialize state visualizer

        Args:
            canvas: tkinter Canvas widget
            available_width: width available for drawing
            available_height: height available for drawing
        """
        self.canvas = canvas
        self.available_width = available_width
        self.available_height = available_height

    def draw_state(self, S, highlights=None):
        """
        Draw the state array S on the canvas with optional highlights

        Args:
            S: list representing the state array
            highlights: dict mapping highlight_type -> index
                       e.g., {'i': 5, 'j': 10, 't': 15, 't_prime': 20}
        """
        self.canvas.delete("all")

        if not S:
            return

        N = len(S)
        highlights = highlights or {}

        # Calculate optimal grid layout
        cols, rows = self._calculate_grid_layout(N)
        cell_size = self._calculate_cell_size(cols, rows)
        padding = 5

        # Draw each cell
        for idx, val in enumerate(S):
            row = idx // cols
            col = idx % cols

            x1 = padding + col * cell_size
            y1 = padding + row * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size

            # Determine cell colors based on highlights
            colors = self._get_cell_colors(idx, highlights)

            # Draw cell rectangle
            width = 2 if self._is_highlighted(idx, highlights) else 1
            self.canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill=colors["fill"],
                outline=colors["outline"],
                width=width,
            )

            # Draw value text if cell is large enough
            if cell_size >= 25:
                self.canvas.create_text(
                    (x1 + x2) / 2,
                    (y1 + y2) / 2,
                    text=str(val),
                    font=("Courier", max(6, cell_size // 3)),
                    fill=colors["text"],
                )

        # Configure scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _calculate_grid_layout(self, N):
        """
        Calculate optimal grid layout for N elements

        Args:
            N: number of elements

        Returns:
            tuple: (cols, rows)
        """
        sqrt_n = int(math.sqrt(N))
        cols = sqrt_n
        rows = sqrt_n

        # Adjust to cover all elements
        while cols * rows < N:
            if cols <= rows:
                cols += 1
            else:
                rows += 1

        return cols, rows

    def _calculate_cell_size(self, cols, rows):
        """
        Calculate cell size based on available space and grid dimensions

        Args:
            cols: number of columns
            rows: number of rows

        Returns:
            int: cell size in pixels
        """
        cell_size = min(self.available_width // cols, self.available_height // rows)
        # Clamp between 15 and 50 pixels
        return max(15, min(50, cell_size))

    def _get_cell_colors(self, idx, highlights):
        """
        Get colors for a cell based on highlights

        Args:
            idx: cell index
            highlights: dict of highlight_type -> index

        Returns:
            dict: colors for fill, outline, text
        """
        # Priority order for highlights (first match wins)
        priority = ["i", "j", "t", "t_prime", "t_double"]

        for highlight_type in priority:
            if highlight_type in highlights and highlights[highlight_type] == idx:
                return self.COLORS[highlight_type]

        return self.COLORS["default"]

    def _is_highlighted(self, idx, highlights):
        """
        Check if a cell is highlighted

        Args:
            idx: cell index
            highlights: dict of highlight_type -> index

        Returns:
            bool: True if cell is highlighted
        """
        return idx in highlights.values()


class LogManager:
    """Manages logging to a text widget"""

    def __init__(self, text_widget):
        """
        Initialize log manager

        Args:
            text_widget: tkinter Text or ScrolledText widget
        """
        self.text_widget = text_widget

    def log(self, message, color="black"):
        """
        Add a log message

        Args:
            message: text to log
            color: text color
        """
        self.text_widget.insert(tk.END, message + "\n", color)
        self.text_widget.see(tk.END)

    def clear(self):
        """Clear all log messages"""
        self.text_widget.delete(1.0, tk.END)

    def log_ksa_start(self, N, key):
        """Log KSA initialization"""
        self.log("=" * 60, "blue")
        self.log("INICIANDO KSA (Key Scheduling Algorithm)", "blue")
        self.log(f"Tamaño del estado: N = {N}", "blue")
        self.log(f"Clave: '{key}'", "blue")
        self.log("=" * 60, "blue")

    def log_ksa_step(self, i, j, N, key_idx):
        """Log a KSA mixing step"""
        self.log(
            f"  i={i:3d}: j = (j + S[{i}] + K[{key_idx}]) mod {N} = {j:3d}, swap S[{i}]↔S[{j}]"
        )

    def log_ksa_complete(self):
        """Log KSA completion"""
        self.log("\n✓ KSA completado - Estado inicializado y mezclado", "green")

    def log_prga_start(self):
        """Log PRGA start"""
        self.log("\n" + "=" * 60, "purple")
        self.log("INICIANDO PRGA (Pseudo Random Generation Algorithm)", "purple")
        self.log("=" * 60, "purple")

    def log_prga_step(self, step_num, result, plain_byte, cipher_byte, printable_char):
        """
        Log a PRGA step

        Args:
            step_num: step number (1-indexed)
            result: dict from prga_step() containing algorithm details
            plain_byte: plaintext byte value
            cipher_byte: ciphertext byte value
            printable_char: printable character for display
        """
        self.log(f"\n--- Paso {step_num} ---")

        if result["details"]["algorithm"] == "RC4":
            self._log_rc4_step(result)
        else:
            self._log_rc4plus_step(result)

        # Log XOR operation
        self.log(f"Plaintext[{step_num - 1}] = '{printable_char}' = {plain_byte}")
        self.log(
            f"Ciphertext[{step_num - 1}] = {plain_byte} ⊕ {result['output_byte']} = {cipher_byte} (0x{cipher_byte:02x})"
        )

    def _log_rc4_step(self, result):
        """Log RC4 classic step details"""
        N = result.get('N', 256)
        self.log(f"i = (i + 1) mod {N} = {result['i']}")
        self.log(f"j = (j + S[i]) mod {N} = {result['j']}")
        self.log(f"Swap: {result['details']['swap']}")
        self.log(f"t = (S[i] + S[j]) mod {N} = {result['t']}")
        self.log(f"Output = S[t] = S[{result['t']}] = {result['output_byte']}")

    def _log_rc4plus_step(self, result):
        """Log RC4+ step details"""
        N = result.get('N', 256)
        self.log(f"i (after) = (i + 1) mod {N} = {result['i']}")
        self.log(f"j (after) = (j + S[i]) mod {N} = {result['j']}")
        self.log(f"Swap: {result['details']['swap']}")
        self.log(f"t = (S[i] + S[j]) mod {N} = {result['t']}")
        self.log(f"idx1 = ((i>>3) XOR (j<<5)) & 0xFF = {result['idx1']}")
        self.log(f"idx2 = ((i<<5) XOR (j>>3)) & 0xFF = {result['idx2']}")
        self.log(
            f"t_prime = (S[idx1] + S[idx2]) mod {N} XOR 0xAA = {result['t_prime']}"
        )
        self.log(f"t_double = (j + S[j]) mod {N} = {result['t_double']}")
        self.log(
            f"Output = ((S[t] + S[t_prime]) mod {N}) XOR S[t_double] = {result['output_byte']}"
        )

    def log_prga_complete(self):
        """Log PRGA completion"""
        self.log("\n✓ PRGA completado - Todos los bytes procesados", "green")

    def log_results(self, plaintext, keystream, ciphertext):
        """
        Log final results

        Args:
            plaintext: original plaintext string
            keystream: list of keystream bytes
            ciphertext: list of ciphertext bytes
        """
        self.log("\n" + "=" * 60, "green")
        self.log("RESULTADOS FINALES", "green")
        self.log("=" * 60, "green")
        self.log(f"Texto original: {plaintext}")
        self.log(f"Keystream: {' '.join([f'{b:02x}' for b in keystream])}")
        self.log(f"Cifrado (hex): {' '.join([f'{b:02x}' for b in ciphertext])}")
        self.log("=" * 60, "green")
