# RC4+ Stream Cipher: Herramienta de Visualización Educativa y Análisis de Vulnerabilidades

## Resumen

Este proyecto implementa una herramienta educativa interactiva para el análisis y visualización del algoritmo de cifrado de flujo RC4 y su variante mejorada RC4+ (Polak & Boryczka, 2019). La aplicación permite estudiar tanto el funcionamiento interno de estos algoritmos como sus vulnerabilidades de seguridad mediante la implementación de un ataque de recuperación de estado basado en Búsqueda Tabú.

## Motivación Académica

El cifrado RC4, aunque ampliamente utilizado históricamente en protocolos como WEP, WPA y SSL/TLS, presenta vulnerabilidades conocidas que lo hacen inadecuado para aplicaciones de seguridad modernas. RC4+ fue propuesto como una mejora para mitigar algunas de estas debilidades mediante la introducción de mayor complejidad en el generador pseudoaleatorio (PRGA).

Este trabajo tiene como objetivo:
1. **Visualizar** el funcionamiento interno de RC4 y RC4+ para fines educativos
2. **Implementar** el ataque de recuperación de estado mediante Búsqueda Tabú descrito por Polak & Boryczka (2019)
3. **Analizar** experimentalmente la resistencia de RC4+ frente a ataques criptoanalíticos
4. **Demostrar** las diferencias arquitecturales entre RC4 clásico y RC4+

## Arquitectura del Código

El proyecto está organizado en una arquitectura modular que separa responsabilidades y facilita la extensibilidad:

### 📁 Estructura de Archivos

```
rc4plus/
├── main.py                    # Aplicación principal y lógica de control
├── rc4/
│   ├── rc4_crypto.py         # Implementaciones de algoritmos RC4 y RC4+
│   ├── rc4_visualization.py  # Visualización del estado y logging
│   ├── rc4_ui.py            # Componentes de interfaz de usuario
│   └── test_rc4.py          # Tests unitarios de los algoritmos
├── tabu_search/
│   ├── tabu_logic.py        # Motor de Búsqueda Tabú (configuración Z2)
│   └── tabu_gui.py          # Interfaz gráfica del ataque
├── utils/
│   └── utils.py             # Utilidades auxiliares
├── requirements.txt         # Dependencias del proyecto
└── README.md               # Este archivo
```

### 🔧 Módulos

#### `rc4_crypto.py` - Motor Criptográfico
- **`RC4Engine`**: Clase base para motores RC4
  - `ksa(key)`: Key Scheduling Algorithm
  - `reset_prga()`: Reiniciar índices PRGA
  
- **`RC4Classic`**: Implementación del PRGA clásico de RC4
  - `prga_step()`: Genera un byte de keystream usando RC4 clásico
  
- **`RC4Plus`**: Implementación del PRGA de RC4+ (Polak & Boryczka 2019)
  - `prga_step()`: Genera un byte de keystream usando RC4+ (Algorithm 1)
  - Requiere N=256
  
- **Funciones auxiliares**:
  - `encrypt_decrypt(plaintext_bytes, keystream)`: XOR para cifrar/descifrar
  - `generate_keystream(engine, length)`: Genera keystream de longitud especificada

#### `rc4_visualization.py` - Visualización y Logging
- **`StateVisualizer`**: Dibuja el estado S-Box en un canvas
  - `draw_state(S, highlights)`: Dibuja el array de estado con resaltado de índices
  - Colores configurables para i, j, t, t_prime, t_double
  - Layout automático en cuadrícula
  
- **`LogManager`**: Gestiona el logging de operaciones
  - `log(message, color)`: Añade mensaje al log
  - `log_ksa_start/step/complete()`: Logging específico de KSA
  - `log_prga_start/step/complete()`: Logging específico de PRGA
  - `log_results()`: Muestra resultados finales

#### `rc4_ui.py` - Componentes de Interfaz
- **`ControlPanel`**: Panel de controles superiores
  - Selector de tamaño de estado (N)
  - Input de clave y texto plano
  - Selector de algoritmo (RC4 / RC4+)
  - Control de velocidad de animación
  
- **`ButtonPanel`**: Panel de botones de acción
  - Inicializar (KSA)
  - Ejecutar PRGA paso a paso
  - Ejecutar automático
  - Detener / Reset
  - Test RC4+
  
- **`ResultPanel`**: Panel de visualización de resultados
  - Texto original
  - Keystream (hex)
  - Texto cifrado (hex)
  - Texto cifrado (ASCII/latin-1)
  
- **`StateVariablesPanel`**: Panel de variables de estado actuales
  - Valores de i, j, output

#### `rc4_visual.py` - Aplicación Principal
- **`RC4Visualizer`**: Clase principal de la aplicación
  - Coordina todos los módulos
  - Gestiona el estado de la aplicación
  - Controla el flujo de ejecución (KSA, PRGA, animaciones)
  - Implementa callbacks para eventos de UI

## 🚀 Uso

### Ejecutar la aplicación
```bash
python3 main.py
```

### Flujo básico de uso
1. **Seleccionar algoritmo**: RC4 o RC4+ (por defecto RC4+)
2. **Configurar parámetros**:
   - Tamaño del estado N (64, 128, 256, 512)
   - Clave de cifrado
   - Texto a cifrar
   - Velocidad de animación
3. **Inicializar (KSA)**: Click en "Inicializar (KSA)" para mezclar el estado
4. **Ejecutar PRGA**: 
   - "Paso a Paso": Ejecuta un byte a la vez
   - "Automático": Ejecuta todos los bytes con animación
5. **Ver resultados**: Keystream y texto cifrado se muestran en la columna derecha

### Características especiales

#### RC4+ (Polak & Boryczka 2019)
- Requiere N=256 (forzado automáticamente)
- Implementa Algorithm 1 del paper:
  - Cálculo de t_prime usando índices con shifts y XOR
  - Cálculo de t_double
  - Output = ((S[t] + S[t_prime]) mod 256) XOR S[t_double]
- Resaltado adicional de índices t_prime (verde) y t_double (rosa)

#### Encoding
- Usa `latin-1` para mapeo reversible de bytes
- Permite copiar/pegar texto cifrado y descifrarlo correctamente

#### Test automático
- Botón "Run RC4+ Test" ejecuta un test de consistencia
- Cifra "Plaintext" con clave "Key"
- Descifra y verifica que se recupera el texto original

## 🎨 Código de Colores en la Visualización

- **Azul claro** (i): Índice i actual
- **Coral** (j): Índice j actual  
- **Amarillo** (t): Índice t = (S[i] + S[j])
- **Verde claro** (t_prime): Índice t' en RC4+ 
- **Rosa claro** (t_double): Índice t'' en RC4+

## 📊 Ventajas de la Arquitectura Modular

1. **Separación de responsabilidades**: Cada módulo tiene un propósito claro
2. **Facilidad de prueba**: Los módulos pueden probarse independientemente
3. **Reutilización**: Los componentes pueden usarse en otros proyectos
4. **Mantenibilidad**: Cambios localizados en módulos específicos
5. **Extensibilidad**: Fácil añadir nuevos algoritmos o visualizaciones
6. **Legibilidad**: Código organizado y documentado

## 🔬 Testing

### Probar los módulos individualmente
```bash
# Test del módulo criptográfico
python3 -c "from rc4_crypto import RC4Classic, RC4Plus; print('OK')"

# Test del módulo de visualización
python3 -c "from rc4_visualization import StateVisualizer, LogManager; print('OK')"

# Test del módulo de UI
python3 -c "from rc4_ui import ControlPanel, ButtonPanel; print('OK')"
```

### Test de integración
Usar el botón "Run RC4+ Test" en la aplicación para verificar que el cifrado/descifrado es simétrico.

## 📝 Notas Técnicas

- **KSA**: Común para RC4 y RC4+
- **PRGA**: Diferente entre RC4 (clásico) y RC4+ (Algorithm 1)
- **N=256**: Requerido para RC4+, configurable (64-512) para RC4 clásico
- **Animación**: Velocidad ajustable de 100ms a 2000ms
- **Visualización**: Layout automático en cuadrícula optimizada

## 🐛 Troubleshooting

Si la aplicación no inicia:
```bash
# Verificar que tkinter está instalado
python3 -c "import tkinter; print('tkinter OK')"

# Si falla, instalar tkinter
sudo apt-get install python3-tk  # Ubuntu/Debian
```

## 📊 Ventajas de la Arquitectura Modular

1. **Separación de responsabilidades**: Cada módulo tiene un propósito claramente definido
2. **Facilidad de prueba**: Los módulos pueden probarse independientemente
3. **Reutilización**: Los componentes pueden emplearse en otros proyectos
4. **Mantenibilidad**: Cambios localizados en módulos específicos sin afectar al resto
5. **Extensibilidad**: Fácil añadir nuevos algoritmos o métodos de visualización
6. **Legibilidad**: Código organizado, documentado y autoexplicativo

## 📚 Referencias

1. **Rivest, R. L.** (1987). *The RC4 Encryption Algorithm*. RSA Data Security, Inc.

2. **Polak, A., & Boryczka, M.** (2019). *Tabu Search in Revealing the Internal State of RC4+ Cipher*. In: Rutkowski, L., Scherer, R., Korytkowski, M., Pedrycz, W., Tadeusiewicz, R., Zurada, J. (eds) Artificial Intelligence and Soft Computing. ICAISC 2019. Lecture Notes in Computer Science(), vol 11509. Springer, Cham. https://doi.org/10.1007/978-3-030-20915-5_21

3. **Fluhrer, S., Mantin, I., & Shamir, A.** (2001). *Weaknesses in the Key Scheduling Algorithm of RC4*. In Selected Areas in Cryptography (pp. 1-24). Springer.

4. **AlFardan, N., Bernstein, D. J., Paterson, K. G., Poettering, B., & Schuldt, J. C.** (2013). *On the Security of RC4 in TLS*. In USENIX Security Symposium (pp. 305-320).

## 👤 Autores

**Francisco Rodríguez-Carretero Roldán**  
**Miguel Regidor García**

## 📄 Licencia

Este proyecto ha sido desarrollado con fines educativos y de investigación. 

---

**Advertencia**: Este software se proporciona "tal cual" sin garantías de ningún tipo. Los algoritmos RC4 y RC4+ implementados aquí son únicamente para estudio académico y NO deben emplearse en sistemas de producción o aplicaciones que requieran seguridad criptográfica real.
