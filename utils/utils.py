def show_help_text() -> str:
    texto = """Ayuda: Ataque de Recuperación de Estado (Tabu Search)
Esta herramienta visualiza cómo el algoritmo intenta recuperar una S-Box secreta basándose en la salida interceptada (Keystream).

Nota: Internamente, el algoritmo de búsqueda tabú está configurado utilizando la configuración Z2.

Para una prueba rápida, visible y didáctica de la funcionalidad, utilice los siguientes parámetros predeterminados:
    - Tamaño del Estado (N): 64
    - Longitud de Keystream: 15 bytes"

A continuación se detalla el funcionamiento de la interfaz:

1. Configuración del Ataque
Defina los parámetros para la simulación:

- N Size: El tamaño de la S-Box (espacio de búsqueda).
- Keystream Length: Cantidad de caracteres (bytes) que se generarán para evaluar las soluciones.
- Max Iterations: Límite de intentos antes de detener el algoritmo.
- Modo de Ataque:
  · ⚡ Rápido: El algoritmo corre a máxima velocidad sin pausas. La UI se actualiza cada 500ms, pero el backend procesa iteraciones mucho más rápido. Las visualizaciones pueden no reflejar todos los estados intermedios debido a la alta velocidad de procesamiento.
  · Didáctico: El algoritmo pausa 500ms entre iteraciones para permitir una visualización fluida y educativa de cada paso del proceso.

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

def show_algorithm_info_text() -> str:
    texto = """El proceso de recuperación de la clave se articula mediante una función de fitness, encargada de evaluar la calidad de cada solución candidata. Esta función actúa como un comparador que mide la discrepancia entre la keystream generada por la caja candidata y la keystream objetivo. El algoritmo identifica la solución correcta cuando esta discrepancia es nula, es decir, cuando la salida generada coincide exactamente con la esperada.

Para alcanzar este estado, la Búsqueda Tabú emplea una estrategia dinámica diseñada para evitar el estancamiento en máximos locales. Siguiendo una analogía topológica, mientras que un algoritmo voraz (hill climbing) se detendría al alcanzar la cima de una colina pequeña (creyendo erróneamente que es el punto más alto), la Búsqueda Tabú posee la capacidad de aceptar movimientos hacia soluciones peores.

Esto equivale a descender de la colina para atravesar un valle y poder ascender hacia una montaña más alta (el máximo global). Al permitir temporalmente una disminución en el valor de fitness y bloquear el retorno inmediato a estados anteriores mediante la lista tabú, el sistema garantiza una exploración profunda del espacio de búsqueda.

Es fundamental notar que, debido a las características del cifrado analizado, existe una notable asimetría dimensional; Si se intenta reconstruir un estado interno (S-Box) de 64 bytes utilizando únicamente una referencia de salida de 5 bytes. Dada esta diferencia de entropía, existen múltiples configuraciones iniciales de la caja que pueden derivar en la misma salida final.

Por tanto, es posible que el algoritmo converja y detenga su ejecución al encontrar una caja que genera la keystream correcta (maximizando la función de fitness), aunque dicha caja no sea idéntica bit a bit a la S-Box original, sino una solución matemáticamente equivalente para ese fragmento específico."""
    return texto