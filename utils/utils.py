def show_help_text() -> str:
    texto = """Ayuda: Ataque de Recuperación de Estado (Tabu Search)
Esta herramienta visualiza cómo el algoritmo intenta recuperar una S-Box secreta basándose en la salida interceptada (Keystream).

Nota: Internamente, el algoritmo de búsqueda tabú está configurado utilizando la configuración Z2.

A continuación se detalla el funcionamiento de la interfaz:

1. Configuración del Ataque
Defina los parámetros para la simulación:

- N Size: El tamaño de la S-Box (espacio de búsqueda).
- Keystream Length: Cantidad de caracteres (bytes) que se generarán para evaluar las soluciones.
- Max Iterations: Límite de intentos antes de detener el algoritmo.

2. Funcionamiento (Botón Start Attack)
Al pulsar Start Attack, se desencadena la siguiente secuencia lógica:

- Generación del Objetivo: El sistema crea una Target S-Box (S-Box Secreta) totalmente aleatoria de tamaño N.
- Generación de Pistas: Usando esa S-Box secreta, se genera un Target Output (Keystream) de la longitud especificada. Este es el patrón que el algoritmo debe intentar replicar.
- Inicio del Algoritmo: Se crea una Candidate S-Box inicial aleatoria y comienza el bucle de optimización para intentar transformar esta candidata en la secreta.

3. Visualización de S-Boxes (Paneles Superiores)
- Target S-Box (Izquierda): Representa la S-Box secreta real (el objetivo a alcanzar).
- Candidate S-Box (Derecha): Representa la S-Box "hipotética" que el algoritmo está modificando en tiempo real.

Código de Colores:

- 🟩 Correcto: El valor coincide con la S-Box secreta.
- 🟥 Incorrecto: El valor no coincide.
- 🟧 Fue Correcto: El valor coincidía antes, pero se perdió en un movimiento reciente.
- 🟨 Intercambio Actual: Resalta los elementos que se están intercambiando en este instante.

4. Comparación de Salidas (Keystream Comparison)
En la parte inferior se valida si el ataque está funcionando comparando las salidas:

- Target Output: La salida real generada por la S-Box secreta.
- Current Output: La salida que produce la S-Box candidata en la iteración actual.
- Best Output: La salida de la mejor configuración encontrada hasta el momento.

El ataque tiene éxito cuando el "Best Output" es idéntico al "Target Output".

5. Monitoreo del Progreso (Status)
Este panel muestra métricas numéricas en tiempo real:

- Iteration: El número de intento actual.
- Fitness: La puntuación de error actual (0 indica una coincidencia perfecta).
- Best Fitness: La mejor puntuación obtenida hasta el momento.
- Tabu Size: Cantidad de movimientos que están temporalmente prohibidos en la lista tabú.
"""

    return texto
