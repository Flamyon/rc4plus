#!/usr/bin/env python3
"""
RC4+ Stream Cipher - Visualización Interactiva
Muestra paso a paso el funcionamiento interno del algoritmo
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import time


class RC4PlusVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("RC4+ Stream Cipher - Visualizador Interactivo")
        self.root.geometry("1400x900")
        
        # Variables del algoritmo
        self.N = 256  # Tamaño del estado por defecto
        self.S = []
        self.i = 0
        self.j = 0
        self.key = ""
        self.plaintext = ""
        self.animation_speed = 500  # ms
        self.is_running = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Frame superior - Controles
        control_frame = ttk.LabelFrame(self.root, text="Controles", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Tamaño del estado
        ttk.Label(control_frame, text="Tamaño del Estado (N):").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.size_var = tk.IntVar(value=256)
        size_frame = ttk.Frame(control_frame)
        size_frame.grid(row=0, column=1, padx=5, sticky=tk.W)
        
        ttk.Radiobutton(size_frame, text="64", variable=self.size_var, value=64).pack(side=tk.LEFT)
        ttk.Radiobutton(size_frame, text="128", variable=self.size_var, value=128).pack(side=tk.LEFT)
        ttk.Radiobutton(size_frame, text="256", variable=self.size_var, value=256).pack(side=tk.LEFT)
        ttk.Radiobutton(size_frame, text="512", variable=self.size_var, value=512).pack(side=tk.LEFT)
        
        # Clave
        ttk.Label(control_frame, text="Clave:").grid(row=1, column=0, padx=5, sticky=tk.W)
        self.key_entry = ttk.Entry(control_frame, width=40)
        self.key_entry.grid(row=1, column=1, padx=5, sticky=tk.W)
        self.key_entry.insert(0, "SecretKey")
        
        # Texto a cifrar
        ttk.Label(control_frame, text="Texto:").grid(row=2, column=0, padx=5, sticky=tk.W)
        self.text_entry = ttk.Entry(control_frame, width=40)
        self.text_entry.grid(row=2, column=1, padx=5, sticky=tk.W)
        self.text_entry.insert(0, "Hello RC4+")
        
        # Velocidad de animación
        ttk.Label(control_frame, text="Velocidad:").grid(row=3, column=0, padx=5, sticky=tk.W)
        self.speed_label = ttk.Label(control_frame, text="500 ms")
        self.speed_label.grid(row=3, column=2, padx=5)
        self.speed_scale = ttk.Scale(control_frame, from_=100, to=2000, orient=tk.HORIZONTAL, 
                                     command=self.update_speed, length=200)
        self.speed_scale.set(500)
        self.speed_scale.grid(row=3, column=1, padx=5, sticky=tk.W)
        
        # Botones
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="Inicializar (KSA)", command=self.init_ksa).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Ejecutar PRGA Paso a Paso", command=self.step_prga).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Ejecutar Automático", command=self.auto_run).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Detener", command=self.stop).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset", command=self.reset).pack(side=tk.LEFT, padx=5)
        
        # Frame principal - dividido en dos columnas
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Columna izquierda - Estado interno
        left_frame = ttk.LabelFrame(main_frame, text="Estado Interno (S-Box)", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Canvas para visualizar el estado
        canvas_frame = ttk.Frame(left_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.state_canvas = tk.Canvas(canvas_frame, bg="white", height=400)
        scrollbar_y = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.state_canvas.yview)
        scrollbar_x = ttk.Scrollbar(left_frame, orient=tk.HORIZONTAL, command=self.state_canvas.xview)
        
        self.state_canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.state_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_x.pack(fill=tk.X)
        
        # Variables de estado actual
        state_vars_frame = ttk.LabelFrame(left_frame, text="Variables de Estado", padding=5)
        state_vars_frame.pack(fill=tk.X, pady=5)
        
        self.var_i_label = ttk.Label(state_vars_frame, text="i = 0", font=("Courier", 12, "bold"))
        self.var_i_label.pack(side=tk.LEFT, padx=10)
        
        self.var_j_label = ttk.Label(state_vars_frame, text="j = 0", font=("Courier", 12, "bold"))
        self.var_j_label.pack(side=tk.LEFT, padx=10)
        
        self.output_label = ttk.Label(state_vars_frame, text="Output = -", font=("Courier", 12, "bold"))
        self.output_label.pack(side=tk.LEFT, padx=10)
        
        # Columna derecha - Log de operaciones y resultado
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # Log de operaciones
        log_frame = ttk.LabelFrame(right_frame, text="Log de Operaciones", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=50, height=20, 
                                                   font=("Courier", 9), wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Resultado
        result_frame = ttk.LabelFrame(right_frame, text="Resultado", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        ttk.Label(result_frame, text="Texto Original:").pack(anchor=tk.W)
        self.original_text = tk.Text(result_frame, height=2, font=("Courier", 10))
        self.original_text.pack(fill=tk.X, pady=2)
        
        ttk.Label(result_frame, text="Keystream (hex):").pack(anchor=tk.W)
        self.keystream_text = tk.Text(result_frame, height=2, font=("Courier", 10))
        self.keystream_text.pack(fill=tk.X, pady=2)
        
        ttk.Label(result_frame, text="Texto Cifrado (hex):").pack(anchor=tk.W)
        self.cipher_text = tk.Text(result_frame, height=2, font=("Courier", 10))
        self.cipher_text.pack(fill=tk.X, pady=2)
        
        ttk.Label(result_frame, text="Texto Cifrado (ASCII):").pack(anchor=tk.W)
        self.cipher_ascii_text = tk.Text(result_frame, height=2, font=("Courier", 10))
        self.cipher_ascii_text.pack(fill=tk.X, pady=2)
        
        # Historial para PRGA
        self.prga_step = 0
        self.keystream = []
        self.ciphertext = []
        
    def update_speed(self, value):
        self.animation_speed = int(float(value))
        self.speed_label.config(text=f"{self.animation_speed} ms")
        
    def log(self, message, color="black"):
        self.log_text.insert(tk.END, message + "\n", color)
        self.log_text.see(tk.END)
        self.root.update()
        
    def init_ksa(self):
        """Key Scheduling Algorithm - Inicialización"""
        self.stop()
        self.N = self.size_var.get()
        self.key = self.key_entry.get()
        self.plaintext = self.text_entry.get()
        
        if not self.key:
            self.log("ERROR: Debe ingresar una clave", "red")
            return
            
        self.log("="*60, "blue")
        self.log(f"INICIANDO KSA (Key Scheduling Algorithm)", "blue")
        self.log(f"Tamaño del estado: N = {self.N}", "blue")
        self.log(f"Clave: '{self.key}'", "blue")
        self.log("="*60, "blue")
        
        # Inicializar S
        self.S = list(range(self.N))
        self.log(f"\nPaso 1: Inicializar S[i] = i para i = 0..{self.N-1}")
        self.draw_state()
        self.root.after(self.animation_speed)
        
        # Convertir clave a bytes
        key_bytes = [ord(c) for c in self.key]
        key_length = len(key_bytes)
        
        self.log(f"\nPaso 2: Mezclar el estado usando la clave")
        self.log(f"Longitud de la clave: {key_length} bytes")
        
        # KSA - mezclar
        j = 0
        for i in range(self.N):
            j = (j + self.S[i] + key_bytes[i % key_length]) % self.N
            self.S[i], self.S[j] = self.S[j], self.S[i]
            
            if i < 10 or i % (self.N // 10) == 0:  # Mostrar algunos pasos
                self.log(f"  i={i:3d}: j = (j + S[{i}] + K[{i % key_length}]) mod {self.N} = {j:3d}, swap S[{i}]↔S[{j}]")
                self.i = i
                self.j = j
                self.var_i_label.config(text=f"i = {i}")
                self.var_j_label.config(text=f"j = {j}")
                self.draw_state(highlight_i=i, highlight_j=j)
                self.root.update()
                time.sleep(self.animation_speed / 2000.0)
        
        self.log("\n✓ KSA completado - Estado inicializado y mezclado", "green")
        
        # Reset para PRGA
        self.i = 0
        self.j = 0
        self.prga_step = 0
        self.keystream = []
        self.ciphertext = []
        
        self.var_i_label.config(text=f"i = 0")
        self.var_j_label.config(text=f"j = 0")
        self.output_label.config(text=f"Output = -")
        
        self.draw_state()
        
        # Mostrar texto original
        self.original_text.delete(1.0, tk.END)
        self.original_text.insert(1.0, self.plaintext)
        
    def step_prga(self):
        """Pseudo Random Generation Algorithm - Un paso"""
        if not self.S:
            self.log("ERROR: Primero debe ejecutar KSA (Inicializar)", "red")
            return
            
        if self.prga_step == 0:
            self.log("\n" + "="*60, "purple")
            self.log("INICIANDO PRGA (Pseudo Random Generation Algorithm)", "purple")
            self.log("="*60, "purple")
            
        if self.prga_step >= len(self.plaintext):
            self.log("\n✓ PRGA completado - Todos los bytes procesados", "green")
            self.display_results()
            return
            
        # RC4+ PRGA
        self.i = (self.i + 1) % self.N
        self.j = (self.j + self.S[self.i]) % self.N
        
        self.log(f"\n--- Paso {self.prga_step + 1} ---")
        self.log(f"i = (i + 1) mod {self.N} = {self.i}")
        self.log(f"j = (j + S[i]) mod {self.N} = (j + S[{self.i}]) mod {self.N} = {self.j}")
        
        # Swap
        self.S[self.i], self.S[self.j] = self.S[self.j], self.S[self.i]
        self.log(f"Swap: S[{self.i}] ↔ S[{self.j}]")
        
        # RC4+ improvement: second swap
        k = (self.S[self.i] + self.S[self.j]) % self.N
        self.log(f"k = (S[i] + S[j]) mod {self.N} = ({self.S[self.i]} + {self.S[self.j]}) mod {self.N} = {k}")
        
        # Output byte (RC4+ uses different output)
        t = (self.S[self.i] + self.S[self.j] + self.S[k]) % self.N
        output_byte = self.S[t]
        
        self.log(f"t = (S[i] + S[j] + S[k]) mod {self.N} = {t}")
        self.log(f"Output = S[t] = S[{t}] = {output_byte}")
        
        # XOR con el texto plano
        plain_byte = ord(self.plaintext[self.prga_step])
        cipher_byte = plain_byte ^ output_byte
        
        self.log(f"Plaintext[{self.prga_step}] = '{self.plaintext[self.prga_step]}' = {plain_byte}")
        self.log(f"Ciphertext[{self.prga_step}] = {plain_byte} ⊕ {output_byte} = {cipher_byte} (0x{cipher_byte:02x})")
        
        self.keystream.append(output_byte)
        self.ciphertext.append(cipher_byte)
        
        # Actualizar UI
        self.var_i_label.config(text=f"i = {self.i}")
        self.var_j_label.config(text=f"j = {self.j}")
        self.output_label.config(text=f"Output = {output_byte}")
        
        self.draw_state(highlight_i=self.i, highlight_j=self.j, highlight_k=k, highlight_t=t)
        
        self.prga_step += 1
        
        # Actualizar resultados parciales
        self.update_partial_results()
        
    def auto_run(self):
        """Ejecutar automáticamente hasta completar"""
        if not self.S:
            self.log("ERROR: Primero debe ejecutar KSA (Inicializar)", "red")
            return
            
        self.is_running = True
        self.auto_step()
        
    def auto_step(self):
        if self.is_running and self.prga_step < len(self.plaintext):
            self.step_prga()
            self.root.after(self.animation_speed, self.auto_step)
        elif self.prga_step >= len(self.plaintext):
            self.is_running = False
            
    def stop(self):
        """Detener ejecución automática"""
        self.is_running = False
        
    def reset(self):
        """Reiniciar todo"""
        self.stop()
        self.S = []
        self.i = 0
        self.j = 0
        self.prga_step = 0
        self.keystream = []
        self.ciphertext = []
        
        self.log_text.delete(1.0, tk.END)
        self.original_text.delete(1.0, tk.END)
        self.keystream_text.delete(1.0, tk.END)
        self.cipher_text.delete(1.0, tk.END)
        self.cipher_ascii_text.delete(1.0, tk.END)
        
        self.var_i_label.config(text="i = 0")
        self.var_j_label.config(text="j = 0")
        self.output_label.config(text="Output = -")
        
        self.state_canvas.delete("all")
        self.log("Sistema reiniciado", "blue")
        
    def draw_state(self, highlight_i=None, highlight_j=None, highlight_k=None, highlight_t=None):
        """Dibujar el estado interno S"""
        self.state_canvas.delete("all")
        
        if not self.S:
            return
            
        # Determinar disposición cuadrada óptima
        import math
        sqrt_n = int(math.sqrt(self.N))
        
        # Buscar el arreglo más cercano a un cuadrado
        cols = sqrt_n
        rows = sqrt_n
        
        # Ajustar para cubrir todos los elementos
        while cols * rows < self.N:
            if cols <= rows:
                cols += 1
            else:
                rows += 1
        
        # Calcular tamaño de celda para ajustarse al canvas
        available_width = 800
        available_height = 600
        cell_size = min(available_width // cols, available_height // rows)
        cell_size = max(15, min(50, cell_size))  # Entre 15 y 50 pixels
        
        padding = 5
        
        for idx, val in enumerate(self.S):
            row = idx // cols
            col = idx % cols
            
            x1 = padding + col * cell_size
            y1 = padding + row * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size
            
            # Color de fondo
            fill_color = "white"
            outline_color = "gray"
            text_color = "black"
            
            if idx == highlight_i:
                fill_color = "lightblue"
                outline_color = "blue"
                text_color = "blue"
            elif idx == highlight_j:
                fill_color = "lightcoral"
                outline_color = "red"
                text_color = "red"
            elif idx == highlight_k:
                fill_color = "lightgreen"
                outline_color = "green"
                text_color = "green"
            elif idx == highlight_t:
                fill_color = "lightyellow"
                outline_color = "orange"
                text_color = "orange"
                
            # Dibujar celda
            self.state_canvas.create_rectangle(x1, y1, x2, y2, 
                                               fill=fill_color, 
                                               outline=outline_color,
                                               width=2 if idx in [highlight_i, highlight_j, highlight_k, highlight_t] else 1)
            
            # Mostrar valor si la celda es grande
            if cell_size >= 25:
                self.state_canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, 
                                             text=str(val), 
                                             font=("Courier", max(6, cell_size // 3)),
                                             fill=text_color)
        
        # Configurar scroll region
        self.state_canvas.configure(scrollregion=self.state_canvas.bbox("all"))
        
    def update_partial_results(self):
        """Actualizar resultados parciales"""
        # Keystream
        self.keystream_text.delete(1.0, tk.END)
        keystream_hex = ' '.join([f'{b:02x}' for b in self.keystream])
        self.keystream_text.insert(1.0, keystream_hex)
        
        # Ciphertext
        self.cipher_text.delete(1.0, tk.END)
        cipher_hex = ' '.join([f'{b:02x}' for b in self.ciphertext])
        self.cipher_text.insert(1.0, cipher_hex)
        
        # Ciphertext ASCII
        self.cipher_ascii_text.delete(1.0, tk.END)
        cipher_ascii = ''.join([chr(b) if 32 <= b < 127 else '.' for b in self.ciphertext])
        self.cipher_ascii_text.insert(1.0, cipher_ascii)
        
    def display_results(self):
        """Mostrar resultados finales"""
        self.update_partial_results()
        
        self.log("\n" + "="*60, "green")
        self.log("RESULTADOS FINALES", "green")
        self.log("="*60, "green")
        self.log(f"Texto original: {self.plaintext}")
        self.log(f"Keystream: {' '.join([f'{b:02x}' for b in self.keystream])}")
        self.log(f"Cifrado (hex): {' '.join([f'{b:02x}' for b in self.ciphertext])}")
        self.log("="*60, "green")


def main():
    root = tk.Tk()
    app = RC4PlusVisualizer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
