"""
UI Components Module
Contains reusable UI widgets and helpers for the RC4 visualizer
"""

import tkinter as tk
from tkinter import ttk


class ControlPanel:
    """Control panel containing all input controls"""
    
    def __init__(self, parent, on_algorithm_change_callback):
        """
        Initialize control panel
        
        Args:
            parent: parent tkinter widget
            on_algorithm_change_callback: function to call when algorithm changes
        """
        self.frame = ttk.LabelFrame(parent, text="Controles", padding=10)
        self.on_algorithm_change = on_algorithm_change_callback
        
        # Variables
        self.size_var = tk.IntVar(value=256)
        self.algorithm_var = tk.StringVar(value="RC4+")
        self.animation_speed = 500
        
        # Keep references to widgets that need to be enabled/disabled
        self.size_radios = []
        
        self._setup_controls()
    
    def _setup_controls(self):
        """Setup all control widgets"""
        # State size selection
        ttk.Label(self.frame, text="Tamaño del Estado (N):").grid(
            row=0, column=0, padx=5, sticky=tk.W
        )
        size_frame = ttk.Frame(self.frame)
        size_frame.grid(row=0, column=1, padx=5, sticky=tk.W)
        
        for value in [64, 128, 256, 512]:
            r = ttk.Radiobutton(
                size_frame, text=str(value),
                variable=self.size_var, value=value
            )
            r.pack(side=tk.LEFT)
            self.size_radios.append(r)
        
        # Key input
        ttk.Label(self.frame, text="Clave:").grid(
            row=1, column=0, padx=5, sticky=tk.W
        )
        self.key_entry = ttk.Entry(self.frame, width=40)
        self.key_entry.grid(row=1, column=1, padx=5, sticky=tk.W)
        self.key_entry.insert(0, "SecretKey")
        
        # Algorithm selector
        ttk.Label(self.frame, text="Algoritmo:").grid(
            row=1, column=2, padx=5, sticky=tk.W
        )
        self.algorithm_combo = ttk.Combobox(
            self.frame, width=8, state='readonly',
            values=("RC4", "RC4+"), textvariable=self.algorithm_var
        )
        self.algorithm_combo.grid(row=1, column=3, padx=5, sticky=tk.W)
        self.algorithm_combo.bind(
            '<<ComboboxSelected>>',
            lambda e: self.on_algorithm_change()
        )
        
        # Plaintext input
        ttk.Label(self.frame, text="Texto:").grid(
            row=2, column=0, padx=5, sticky=tk.W
        )
        self.text_entry = ttk.Entry(self.frame, width=40)
        self.text_entry.grid(row=2, column=1, padx=5, sticky=tk.W)
        self.text_entry.insert(0, "Hello RC4")
        
        # Speed control
        ttk.Label(self.frame, text="Velocidad:").grid(
            row=3, column=0, padx=5, sticky=tk.W
        )
        self.speed_label = ttk.Label(self.frame, text="500 ms")
        self.speed_label.grid(row=3, column=2, padx=5)
        self.speed_scale = ttk.Scale(
            self.frame, from_=100, to=2000, orient=tk.HORIZONTAL,
            command=self._update_speed, length=200
        )
        self.speed_scale.set(500)
        self.speed_scale.grid(row=3, column=1, padx=5, sticky=tk.W)
    
    def _update_speed(self, value):
        """Update animation speed"""
        self.animation_speed = int(float(value))
        self.speed_label.config(text=f"{self.animation_speed} ms")
    
    def pack(self, **kwargs):
        """Pack the control panel frame"""
        self.frame.pack(**kwargs)
    
    def get_state_size(self):
        """Get selected state size"""
        return self.size_var.get()
    
    def set_state_size(self, value):
        """Set state size"""
        self.size_var.set(value)
    
    def get_algorithm(self):
        """Get selected algorithm"""
        return self.algorithm_var.get()
    
    def set_algorithm(self, value):
        """Set algorithm"""
        self.algorithm_var.set(value)
    
    def get_key(self):
        """Get key from entry"""
        return self.key_entry.get()
    
    def set_key(self, key):
        """Set key in entry"""
        self.key_entry.delete(0, tk.END)
        self.key_entry.insert(0, key)
    
    def get_plaintext(self):
        """Get plaintext from entry"""
        return self.text_entry.get()
    
    def set_plaintext(self, text):
        """Set plaintext in entry"""
        self.text_entry.delete(0, tk.END)
        self.text_entry.insert(0, text)
    
    def get_animation_speed(self):
        """Get animation speed in ms"""
        return self.animation_speed
    
    def enable_size_radios(self, enable=True):
        """Enable or disable size radio buttons"""
        state = 'normal' if enable else 'disabled'
        for radio in self.size_radios:
            radio.configure(state=state)


class ButtonPanel:
    """Panel containing action buttons"""
    
    def __init__(self, parent, callbacks):
        """
        Initialize button panel
        
        Args:
            parent: parent widget (typically ControlPanel.frame)
            callbacks: dict mapping button_name -> callback_function
        """
        self.frame = ttk.Frame(parent)
        self.callbacks = callbacks
        
        self._setup_buttons()
    
    def _setup_buttons(self):
        """Setup all buttons"""
        buttons = [
            ("Inicializar (KSA)", "init_ksa"),
            ("Ejecutar PRGA Paso a Paso", "step_prga"),
            ("Ejecutar Automático", "auto_run"),
            ("Detener", "stop"),
            ("Reset", "reset"),
            ("Run RC4+ Test", "run_test"),
        ]
        
        for text, callback_key in buttons:
            ttk.Button(
                self.frame, text=text,
                command=self.callbacks.get(callback_key, lambda: None)
            ).pack(side=tk.LEFT, padx=5)
    
    def grid(self, **kwargs):
        """Grid the button panel frame"""
        self.frame.grid(**kwargs)


class ResultPanel:
    """Panel displaying results"""
    
    def __init__(self, parent):
        """
        Initialize result panel
        
        Args:
            parent: parent tkinter widget
        """
        self.frame = ttk.LabelFrame(parent, text="Resultado", padding=10)
        
        self._setup_result_fields()
    
    def _setup_result_fields(self):
        """Setup result display fields"""
        # Original text
        ttk.Label(self.frame, text="Texto Original:").pack(anchor=tk.W)
        self.original_text = tk.Text(self.frame, height=2, font=("Courier", 10))
        self.original_text.pack(fill=tk.X, pady=2)
        
        # Keystream hex
        ttk.Label(self.frame, text="Keystream (hex):").pack(anchor=tk.W)
        self.keystream_text = tk.Text(self.frame, height=2, font=("Courier", 10))
        self.keystream_text.pack(fill=tk.X, pady=2)
        
        # Ciphertext hex
        ttk.Label(self.frame, text="Texto Cifrado (hex):").pack(anchor=tk.W)
        self.cipher_text = tk.Text(self.frame, height=2, font=("Courier", 10))
        self.cipher_text.pack(fill=tk.X, pady=2)
        
        # Ciphertext ASCII
        ttk.Label(self.frame, text="Texto Cifrado (ASCII):").pack(anchor=tk.W)
        self.cipher_ascii_text = tk.Text(self.frame, height=2, font=("Courier", 10))
        self.cipher_ascii_text.pack(fill=tk.X, pady=2)
    
    def pack(self, **kwargs):
        """Pack the result panel frame"""
        self.frame.pack(**kwargs)
    
    def update_results(self, plaintext="", keystream=None, ciphertext=None):
        """
        Update all result fields
        
        Args:
            plaintext: original plaintext string
            keystream: list of keystream bytes
            ciphertext: list of ciphertext bytes
        """
        keystream = keystream or []
        ciphertext = ciphertext or []
        
        # Original text
        self.original_text.delete(1.0, tk.END)
        self.original_text.insert(1.0, plaintext)
        
        # Keystream hex
        self.keystream_text.delete(1.0, tk.END)
        keystream_hex = ' '.join([f'{b:02x}' for b in keystream])
        self.keystream_text.insert(1.0, keystream_hex)
        
        # Ciphertext hex
        self.cipher_text.delete(1.0, tk.END)
        cipher_hex = ' '.join([f'{b:02x}' for b in ciphertext])
        self.cipher_text.insert(1.0, cipher_hex)
        
        # Ciphertext ASCII (using latin-1 for reversibility)
        self.cipher_ascii_text.delete(1.0, tk.END)
        try:
            cipher_ascii = bytes(ciphertext).decode('latin-1')
        except Exception:
            cipher_ascii = ''.join([chr(b) if 32 <= b < 127 else '.' for b in ciphertext])
        self.cipher_ascii_text.insert(1.0, cipher_ascii)
    
    def clear(self):
        """Clear all result fields"""
        self.original_text.delete(1.0, tk.END)
        self.keystream_text.delete(1.0, tk.END)
        self.cipher_text.delete(1.0, tk.END)
        self.cipher_ascii_text.delete(1.0, tk.END)


class StateVariablesPanel:
    """Panel displaying current state variables"""
    
    def __init__(self, parent):
        """
        Initialize state variables panel
        
        Args:
            parent: parent tkinter widget
        """
        self.frame = ttk.LabelFrame(parent, text="Variables de Estado", padding=5)
        
        self._setup_labels()
    
    def _setup_labels(self):
        """Setup variable labels"""
        self.var_i_label = ttk.Label(
            self.frame, text="i = 0",
            font=("Courier", 12, "bold")
        )
        self.var_i_label.pack(side=tk.LEFT, padx=10)
        
        self.var_j_label = ttk.Label(
            self.frame, text="j = 0",
            font=("Courier", 12, "bold")
        )
        self.var_j_label.pack(side=tk.LEFT, padx=10)
        
        self.output_label = ttk.Label(
            self.frame, text="Output = -",
            font=("Courier", 12, "bold")
        )
        self.output_label.pack(side=tk.LEFT, padx=10)
    
    def pack(self, **kwargs):
        """Pack the panel frame"""
        self.frame.pack(**kwargs)
    
    def update_variables(self, i=None, j=None, output=None):
        """
        Update displayed variables
        
        Args:
            i: current i value
            j: current j value
            output: current output byte
        """
        if i is not None:
            self.var_i_label.config(text=f"i = {i}")
        if j is not None:
            self.var_j_label.config(text=f"j = {j}")
        if output is not None:
            self.output_label.config(text=f"Output = {output}")
    
    def reset(self):
        """Reset all variables to initial state"""
        self.var_i_label.config(text="i = 0")
        self.var_j_label.config(text="j = 0")
        self.output_label.config(text="Output = -")
