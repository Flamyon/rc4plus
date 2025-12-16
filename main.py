"""
RC4/RC4+ Stream Cipher - Visualización Interactiva
Muestra paso a paso el funcionamiento interno del algoritmo

Arquitectura modular:
- rc4_crypto.py: Implementaciones de algoritmos RC4 y RC4+
- rc4_visualization.py: Visualización del estado y logging
- rc4_ui.py: Componentes de interfaz de usuario
- rc4_visual.py: Aplicación principal y lógica de control
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import time
import sys

# Importamos la ventana del ataque
from tabu_gui import TabuAttackGUI

from rc4_crypto import RC4Classic, RC4Plus
from rc4_visualization import StateVisualizer, LogManager
from rc4_ui import ControlPanel, ButtonPanel, ResultPanel, StateVariablesPanel

# Ajusta esta ruta si es necesario, o bórrala si los archivos están en la misma carpeta
sys.path.append("/home/mregidorgarcia/proyectos/rc4plus/rc4-tabu-attack/src")


class RC4Visualizer:
    """Main application class for RC4/RC4+ visualization"""

    def __init__(self, root):
        self.root = root
        self.root.title("RC4/RC4+ Stream Cipher - Visualizador Interactivo")
        self.root.geometry("1400x900")

        # Algorithm state
        self.engine = None  # Will be RC4Classic or RC4Plus
        self.plaintext = ""
        self.plaintext_bytes = b""
        self.keystream = []
        self.ciphertext = []
        self.prga_step = 0
        self.is_running = False

        # Setup UI
        self.setup_ui()

        # Initialize with RC4+ and enforce N=256
        self.on_algorithm_change()

    def setup_ui(self):
        """Setup the user interface"""
        # Control panel at top
        self.control_panel = ControlPanel(
            self.root, on_algorithm_change_callback=self.on_algorithm_change
        )
        self.control_panel.pack(fill=tk.X, padx=10, pady=5)

        # Button panel
        button_callbacks = {
            "init_ksa": self.init_ksa,
            "step_prga": self.step_prga,
            "auto_run": self.auto_run,
            "stop": self.stop,
            "reset": self.reset,
            "run_test": self.run_rc4plus_test,
        }
        self.button_panel = ButtonPanel(self.control_panel.frame, button_callbacks)
        self.button_panel.grid(row=4, column=0, columnspan=4, pady=10)

        # --- BOTÓN DE ATAQUE TABÚ ---
        self.tabu_button = tk.Button(
            self.button_panel.frame,
            text="Abrir Ataque Tabu",
            command=self.open_tabu_window,
            background="#d9534f",  # Rojo
            foreground="white",
            font=("Helvetica", 10, "bold"),
        )
        self.tabu_button.pack(side=tk.LEFT, padx=10)
        # ----------------------------

        # Main content area
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left side - State visualization
        self._setup_left_panel(main_frame)

        # Right side - Log and results
        self._setup_right_panel(main_frame)

        # NOTA: Se ha eliminado el 'notebook' (pestañas) para que no salga abajo.

    def _setup_left_panel(self, parent):
        """Setup left panel with state visualization"""
        left_frame = ttk.LabelFrame(parent, text="Estado Interno (S-Box)", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        # Canvas for state visualization
        canvas_frame = ttk.Frame(left_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.state_canvas = tk.Canvas(canvas_frame, bg="white", height=400)
        scrollbar_y = ttk.Scrollbar(
            canvas_frame, orient=tk.VERTICAL, command=self.state_canvas.yview
        )
        scrollbar_x = ttk.Scrollbar(
            left_frame, orient=tk.HORIZONTAL, command=self.state_canvas.xview
        )

        self.state_canvas.configure(
            yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set
        )
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.state_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_x.pack(fill=tk.X)

        # Initialize visualizer
        self.state_visualizer = StateVisualizer(self.state_canvas)

        # State variables display
        self.state_vars_panel = StateVariablesPanel(left_frame)
        self.state_vars_panel.pack(fill=tk.X, pady=5)

    def _setup_right_panel(self, parent):
        """Setup right panel with log and results"""
        right_frame = ttk.Frame(parent)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        # Log area
        log_frame = ttk.LabelFrame(right_frame, text="Log de Operaciones", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        log_text = scrolledtext.ScrolledText(
            log_frame, width=50, height=20, font=("Courier", 9), wrap=tk.WORD
        )
        log_text.pack(fill=tk.BOTH, expand=True)

        # Initialize log manager
        self.log_manager = LogManager(log_text)

        # Results panel
        self.result_panel = ResultPanel(right_frame)
        self.result_panel.pack(fill=tk.BOTH, expand=True, pady=5)

    def on_algorithm_change(self):
        """Handle algorithm selection change"""
        algo = self.control_panel.get_algorithm()

        if algo == "RC4+":
            # RC4+ requires N=256
            if self.control_panel.get_state_size() != 256:
                self.log_manager.log(
                    "WARNING: RC4+ requiere N=256 - forzando N=256", "red"
                )
            self.control_panel.set_state_size(256)
            self.control_panel.enable_size_radios(False)
        else:
            # RC4 allows any N
            self.control_panel.enable_size_radios(True)

    def init_ksa(self):
        """Initialize the cipher using KSA"""
        self.stop()

        # Get parameters
        algo = self.control_panel.get_algorithm()
        key = self.control_panel.get_key()
        self.plaintext = self.control_panel.get_plaintext()

        if not key:
            self.log_manager.log("ERROR: Debe ingresar una clave", "red")
            return

        # Encode plaintext as bytes
        try:
            self.plaintext_bytes = self.plaintext.encode("latin-1")
        except Exception:
            self.plaintext_bytes = self.plaintext.encode("latin-1", "replace")

        # Create engine
        if algo == "RC4+":
            self.engine = RC4Plus()
        else:
            N = self.control_panel.get_state_size()
            self.engine = RC4Classic(N)

        # Log KSA start
        self.log_manager.log_ksa_start(self.engine.N, key)

        # Initialize state
        self.log_manager.log(
            f"\nPaso 1: Inicializar S[i] = i para i = 0..{self.engine.N-1}"
        )
        self.state_visualizer.draw_state(list(range(self.engine.N)))
        self.root.after(self.control_panel.get_animation_speed())
        self.root.update()

        # Run KSA
        self.log_manager.log("\nPaso 2: Mezclar el estado usando la clave")
        self.log_manager.log(f"Longitud de la clave: {len(key)} bytes")

        ksa_steps = self.engine.ksa(key)

        # Visualize some KSA steps
        animation_speed = self.control_panel.get_animation_speed()
        for i, j, description in ksa_steps:
            self.log_manager.log_ksa_step(i, j, self.engine.N, i % len(key))
            self.state_visualizer.draw_state(self.engine.S, highlights={"i": i, "j": j})
            self.state_vars_panel.update_variables(i=i, j=j)
            self.root.update()
            time.sleep(animation_speed / 2000.0)

        self.log_manager.log_ksa_complete()

        # Reset for PRGA
        self.prga_step = 0
        self.keystream = []
        self.ciphertext = []

        self.state_vars_panel.reset()
        self.state_visualizer.draw_state(self.engine.S)

        # Show original text
        self.result_panel.update_results(plaintext=self.plaintext)

    def step_prga(self):
        """Execute one PRGA step"""
        if self.engine is None or not self.engine.S:
            self.log_manager.log(
                "ERROR: Primero debe ejecutar KSA (Inicializar)", "red"
            )
            return

        if self.prga_step == 0:
            self.log_manager.log_prga_start()

        if self.prga_step >= len(self.plaintext_bytes):
            self.log_manager.log_prga_complete()
            self.display_results()
            return

        # Generate keystream byte
        result = self.engine.prga_step()

        # XOR with plaintext
        plain_byte = self.plaintext_bytes[self.prga_step]
        cipher_byte = plain_byte ^ result["output_byte"]

        # Get printable character for logging
        try:
            printable_char = self.plaintext[self.prga_step]
        except Exception:
            printable_char = chr(plain_byte)

        # Log the step
        self.log_manager.log_prga_step(
            self.prga_step + 1, result, plain_byte, cipher_byte, printable_char
        )

        # Store results
        self.keystream.append(result["output_byte"])
        self.ciphertext.append(cipher_byte)

        # Update UI
        self.state_vars_panel.update_variables(
            i=result["i"], j=result["j"], output=result["output_byte"]
        )

        # Build highlights dict
        highlights = {"i": result["i"], "j": result["j"], "t": result["t"]}
        if "t_prime" in result:
            highlights["t_prime"] = result["t_prime"]
        if "t_double" in result:
            highlights["t_double"] = result["t_double"]

        self.state_visualizer.draw_state(self.engine.S, highlights)

        self.prga_step += 1

        # Update partial results
        self.result_panel.update_results(
            self.plaintext, self.keystream, self.ciphertext
        )

    def auto_run(self):
        """Run PRGA automatically until complete"""
        if self.engine is None or not self.engine.S:
            self.log_manager.log(
                "ERROR: Primero debe ejecutar KSA (Inicializar)", "red"
            )
            return

        self.is_running = True
        self.auto_step()

    def auto_step(self):
        """Execute one automatic step"""
        if self.is_running and self.prga_step < len(self.plaintext_bytes):
            self.step_prga()
            self.root.after(self.control_panel.get_animation_speed(), self.auto_step)
        elif self.prga_step >= len(self.plaintext_bytes):
            self.is_running = False

    def stop(self):
        """Stop automatic execution"""
        self.is_running = False

    def reset(self):
        """Reset everything to initial state"""
        self.stop()

        self.engine = None
        self.plaintext = ""
        self.plaintext_bytes = b""
        self.prga_step = 0
        self.keystream = []
        self.ciphertext = []

        self.log_manager.clear()
        self.result_panel.clear()
        self.state_vars_panel.reset()

        self.state_canvas.delete("all")
        self.log_manager.log("Sistema reiniciado", "blue")

    def display_results(self):
        """Display final results"""
        self.result_panel.update_results(
            self.plaintext, self.keystream, self.ciphertext
        )

        self.log_manager.log_results(self.plaintext, self.keystream, self.ciphertext)

    def run_rc4plus_test(self):
        """Run RC4+ test: encrypt then decrypt to verify consistency"""
        self.log_manager.log("\n--- RC4+ TEST START ---", "blue")

        # Set parameters
        self.control_panel.set_algorithm("RC4+")
        self.on_algorithm_change()
        self.control_panel.set_state_size(256)
        self.control_panel.set_key("Key")
        self.control_panel.set_plaintext("Plaintext")

        # Run KSA
        self.init_ksa()

        # Run PRGA
        steps = len(self.plaintext_bytes)
        for _ in range(steps):
            self.step_prga()

        # Log keystream
        keystream_hex = " ".join([f"{b:02x}" for b in self.keystream])
        self.log_manager.log(f"RC4+ keystream: {keystream_hex}", "blue")

        # Decrypt: XOR ciphertext with keystream to recover plaintext
        recovered = bytes([c ^ k for c, k in zip(self.ciphertext, self.keystream)])
        try:
            recovered_text = recovered.decode("latin-1")
        except Exception:
            recovered_text = str(recovered)

        self.log_manager.log(f"Recovered text: {recovered_text}", "blue")

        # Verify
        if recovered_text == "Plaintext":
            self.log_manager.log(
                "✓ Test PASSED: Encryption/Decryption is symmetric", "green"
            )
        else:
            self.log_manager.log("✗ Test FAILED: Recovered text does not match", "red")

        self.log_manager.log("--- RC4+ TEST END ---\n", "blue")

    def open_tabu_window(self):
        """Open Tabu Search attack window"""
        tabu_window = tk.Toplevel(self.root)
        tabu_window.title("Tabu Search State Recovery Attack")
        tabu_window.geometry("1400x900")

        # Create TabuAttackGUI instance - it IS a Frame itself
        tabu_gui = TabuAttackGUI(tabu_window)

        # Pack the TabuAttackGUI directly (it's already a Frame)
        tabu_gui.pack(fill=tk.BOTH, expand=True)

        # Manejar el cierre de la ventana para detener el hilo del ataque
        def on_close():
            # Stop the attack if it's running
            if hasattr(tabu_gui, "_stop_attack"):
                tabu_gui._stop_attack()
            elif hasattr(tabu_gui, "cracker") and tabu_gui.cracker:
                tabu_gui.cracker.stop()

            tabu_window.destroy()

        tabu_window.protocol("WM_DELETE_WINDOW", on_close)


def main():
    """Main entry point"""
    root = tk.Tk()
    RC4Visualizer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
