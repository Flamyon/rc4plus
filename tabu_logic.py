"""
Tabu Search State Recovery Attack - Z2 Configuration
Implements the exact parameters from Polak & Boryczka (2019) Experiment 2, Set Z2
"""

import numpy as np
import threading
import time
from collections import deque
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def rc4_plus_prga(S, length, N):
    """
    Generates a keystream from a given RC4+ state (S-box).
    This centralized function uses modulo N for all index calculations to support
    any S-box size (N).

    Args:
        S (np.array): The S-box state permutation.
        length (int): The number of keystream bytes to generate.
        N (int): The size of the S-box.

    Returns:
        np.array: The generated keystream.
    """
    logger.debug(
        f"rc4_plus_prga called: N={N}, length={length}, S.dtype={S.dtype}, S.shape={S.shape}"
    )
    logger.debug(f"S min={S.min()}, S max={S.max()}")

    S_work = S.copy()
    i, j = 0, 0  # Keep as Python ints
    keystream = np.zeros(length, dtype=np.uint8)

    # Calculate bit width for N to ensure operations stay within bounds
    n_bits = int(np.ceil(np.log2(N)))
    logger.debug(f"n_bits={n_bits}")

    for step in range(length):
        try:
            # RC4+ PRGA step - use Python int to avoid overflow
            i = (i + 1) % N
            j = (j + int(S_work[i])) % N  # Convert to Python int before addition

            # Swap
            S_work[i], S_work[j] = S_work[j], S_work[i]

            # Calculate output indices using modulo N
            t = (int(S_work[i]) + int(S_work[j])) % N  # Use int() for safety

            # RC4+ specific calculations with bit operations scaled to N
            # Shift amounts must be proportional to n_bits, not hardcoded
            shift_right = max(1, n_bits // 3)  # For >>3 equivalent scaled to N
            shift_left = max(1, n_bits - shift_right)  # For <<5 equivalent scaled to N

            if step < 20:  # Extended logging to capture more steps
                logger.debug(
                    f"Step {step}: shift_right={shift_right}, shift_left={shift_left}"
                )

            # Apply bit operations using Python int to prevent overflow
            # Convert to int, perform operations, then modulo to get valid index
            idx1 = ((int(i) >> shift_right) ^ (int(j) << shift_left)) % N
            idx2 = ((int(i) << shift_left) ^ (int(j) >> shift_right)) % N

            if step < 20:
                logger.debug(f"Step {step}: i={i}, j={j}, idx1={idx1}, idx2={idx2}")

            if idx1 >= N or idx2 >= N:
                logger.error(f"INDEX OUT OF BOUNDS! idx1={idx1}, idx2={idx2}, N={N}")
                raise IndexError(
                    f"Calculated index out of bounds: idx1={idx1}, idx2={idx2}, N={N}"
                )

            # The result of the sum is taken modulo N to get a valid index t_prime
            t_prime_val = (int(S_work[idx1]) + int(S_work[idx2])) % N

            # XOR with a value scaled to N (0xAA for N=256, scaled proportionally)
            xor_constant = (0xAA * N) // 256
            t_prime = (t_prime_val ^ xor_constant) % N

            t_double = (int(j) + int(S_work[j])) % N

            if step < 20:
                logger.debug(
                    f"Step {step}: t={t}, t_prime={t_prime}, t_double={t_double}"
                )

            # Generate output byte. Scale to output range [0, 255] for consistency
            # S_work values are in range [0, N-1], scale them to [0, 255]
            if N < 256:
                scale_factor = 256.0 / N
                val1 = (
                    int((S_work[t] * scale_factor + S_work[t_prime] * scale_factor))
                    & 0xFF
                )
                output = (val1 ^ int(S_work[t_double] * scale_factor)) & 0xFF
            else:
                # For N=256, no scaling needed, direct operations
                val1 = (int(S_work[t]) + int(S_work[t_prime])) & 0xFF
                output = (val1 ^ int(S_work[t_double])) & 0xFF

            keystream[step] = output

            if step < 20:  # Extended logging
                logger.debug(f"Step {step}: output={output}")

        except Exception as e:
            logger.error(f"ERROR at step {step}: {e}", exc_info=True)
            logger.error(f"State at error: i={i}, j={j}, N={N}")
            logger.error(f"S_work min={S_work.min()}, max={S_work.max()}")
            raise

    logger.debug(f"rc4_plus_prga completed: keystream[0:5]={keystream[:5]}")
    return keystream


def generate_rc4_plus_keystream(N, length):
    """
    Generate a random RC4+ state and its corresponding keystream.
    Renamed to generate_challenge for clarity in the context of the attack.

    Args:
        N: size of S-box (64, 128, or 256)
        length: number of keystream bytes to generate

    Returns:
        tuple: (target_state, target_keystream)
    """
    logger.info(f"Generating RC4+ keystream: N={N}, length={length}")

    # Validate N is supported
    if N not in [64, 128, 256]:
        raise ValueError(f"N must be 64, 128, or 256. Got: {N}")

    # Generate random permutation with appropriate dtype
    if N <= 256:
        dtype = np.uint8
    else:
        dtype = np.uint16

    target_state = np.arange(N, dtype=dtype)
    np.random.shuffle(target_state)

    logger.debug(
        f"Generated target_state: dtype={target_state.dtype}, shape={target_state.shape}"
    )

    try:
        # Generate keystream using the centralized PRGA function
        target_keystream = rc4_plus_prga(target_state, length, N)
        logger.info("Keystream generation completed successfully")
        return target_state, target_keystream
    except Exception as e:
        logger.error(f"Failed to generate keystream: {e}", exc_info=True)
        raise


# Alias for backward compatibility with GUI if needed
generate_challenge = generate_rc4_plus_keystream


class TabuCracker:
    """
    Tabu Search attack to recover RC4+ internal state (S-box permutation)
    """

    def __init__(self, target_keystream, N=256, target_state=None):
        """
        Initialize Tabu Search cracker

        Args:
            target_keystream: numpy array of target keystream bytes to match
            N: size of S-box (64, 128, or 256)
            target_state: optional, the actual target S-box for visualization
        """
        logger.info(
            f"Initializing TabuCracker: N={N}, keystream_length={len(target_keystream)}"
        )

        # Validate N
        if N not in [64, 128, 256]:
            raise ValueError(f"N must be 64, 128, or 256. Got: {N}")

        self.N = N
        self.target_keystream = np.array(target_keystream, dtype=np.uint8)
        self.keystream_length = len(target_keystream)

        # Store target state for visualization (optional)
        self.target_state = target_state.copy() if target_state is not None else None

        # Z2 Configuration - All parameters scale with N
        self.total_swaps = (N * (N - 1)) // 2
        self.swaps_per_iteration = self.total_swaps // 2
        self.tabu_horizon = self.swaps_per_iteration

        logger.debug(
            f"Tabu parameters: total_swaps={self.total_swaps}, "
            f"swaps_per_iteration={self.swaps_per_iteration}, "
            f"tabu_horizon={self.tabu_horizon}"
        )

        # Pre-compute all possible swaps for efficiency
        self.all_swaps = np.array(
            [(i, j) for i in range(N) for j in range(i + 1, N)], dtype=np.int32
        )

        logger.debug(
            f"all_swaps shape: {self.all_swaps.shape}, max values: {self.all_swaps.max(axis=0)}"
        )

        # Choose appropriate dtype based on N
        dtype = np.uint8 if N <= 256 else np.uint16

        # Initialize with random permutation
        self.current_candidate = np.arange(N, dtype=dtype)
        np.random.shuffle(self.current_candidate)

        self.best_candidate = self.current_candidate.copy()

        logger.info("Calculating initial fitness...")
        self.best_fitness = self._calculate_fitness(self.best_candidate)
        logger.info(f"Initial fitness: {self.best_fitness}/{self.keystream_length}")

        # Tabu list management
        self.tabu_deque = deque(maxlen=self.tabu_horizon)
        self.tabu_set = set()

        # Search state
        self.iteration = 0
        self.current_fitness = self.best_fitness

        # Store current predicted keystream for visualization
        self.current_predicted_keystream = self._generate_keystream(
            self.current_candidate
        )

        # NEW: Track best predicted keystream for visualization
        self.best_predicted_keystream = self.current_predicted_keystream.copy()

        # NEW: Track current swap for visualization
        self.current_swap = None

        # Threading
        self.running = False
        self.thread = None
        self.lock = threading.Lock()

    def _generate_keystream(self, S):
        """
        Generate keystream from a candidate S-box permutation.
        Now calls the centralized, corrected PRGA function.
        """
        logger.debug(
            f"_generate_keystream: S.dtype={S.dtype}, S.shape={S.shape}, N={self.N}"
        )
        return rc4_plus_prga(S, self.keystream_length, self.N)

    def _calculate_fitness(self, candidate):
        """
        Z2 Fitness Function: Byte Fitness
        Counts exact matches between generated and target keystream.
        """
        try:
            candidate_keystream = self._generate_keystream(candidate)
            matches = np.sum(candidate_keystream == self.target_keystream)
            logger.debug(
                f"Fitness calculation: matches={matches}/{self.keystream_length}"
            )
            return int(matches)
        except Exception as e:
            logger.error(f"Error in _calculate_fitness: {e}", exc_info=True)
            raise

    def _get_random_swaps(self):
        """
        Z2 Neighborhood: Generate 50% of all possible swaps randomly
        """
        # Ensure we don't try to select more swaps than exist
        num_swaps = min(self.swaps_per_iteration, len(self.all_swaps))
        selected_indices = np.random.choice(
            len(self.all_swaps), size=num_swaps, replace=False
        )
        swaps = self.all_swaps[selected_indices]
        logger.debug(
            f"_get_random_swaps: num_swaps={num_swaps}, max indices in swaps: {swaps.max(axis=0)}"
        )
        return swaps

    def _apply_swap(self, candidate, i, j):
        """
        Apply swap to candidate and return new state
        """
        # Validate indices are within bounds
        if i >= self.N or j >= self.N or i < 0 or j < 0:
            logger.error(f"Swap indices ({i}, {j}) out of bounds for N={self.N}")
            raise IndexError(f"Swap indices ({i}, {j}) out of bounds for N={self.N}")

        neighbor = candidate.copy()
        neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
        return neighbor

    def _add_to_tabu(self, move):
        """
        Add move to tabu list
        """
        if len(self.tabu_deque) >= self.tabu_horizon:
            oldest = self.tabu_deque[0]
            self.tabu_set.discard(oldest)

        self.tabu_deque.append(move)
        self.tabu_set.add(move)

    def _is_tabu(self, move):
        """
        Check if move is tabu
        """
        return move in self.tabu_set

    def step(self):
        """
        Perform ONE iteration of Tabu Search (Z2 Configuration)
        """
        with self.lock:
            logger.debug(f"Starting iteration {self.iteration + 1}")

            # NUEVO: Guardar el estado ANTES de aplicar cualquier swap
            previous_candidate = self.current_candidate.copy()

            swaps_to_check = self._get_random_swaps()

            best_neighbor = None
            best_neighbor_fitness = -1
            best_move = None

            for swap_idx, (i, j) in enumerate(swaps_to_check):
                move = (int(i), int(j))

                # Validate indices before applying swap
                if i >= self.N or j >= self.N:
                    logger.warning(f"Skipping invalid swap: ({i}, {j}), N={self.N}")
                    continue

                try:
                    neighbor = self._apply_swap(self.current_candidate, i, j)
                    fitness = self._calculate_fitness(neighbor)
                except Exception as e:
                    logger.error(
                        f"Error processing swap ({i}, {j}): {e}", exc_info=True
                    )
                    raise

                is_tabu = self._is_tabu(move)
                aspiration_met = fitness > self.best_fitness

                if not is_tabu or aspiration_met:
                    if fitness > best_neighbor_fitness:
                        best_neighbor_fitness = fitness
                        best_neighbor = neighbor
                        best_move = move

            if best_neighbor is not None:
                # Aplicar el swap al estado interno (NUEVO)
                self.current_candidate = best_neighbor
                self.current_fitness = best_neighbor_fitness
                self.current_swap = best_move

                # Update predicted keystream for visualization
                self.current_predicted_keystream = self._generate_keystream(
                    self.current_candidate
                )

                if best_neighbor_fitness > self.best_fitness:
                    logger.info(
                        f"New best fitness: {best_neighbor_fitness}/{self.keystream_length} "
                        f"(iteration {self.iteration + 1})"
                    )
                    self.best_candidate = best_neighbor.copy()
                    self.best_fitness = best_neighbor_fitness
                    self.best_predicted_keystream = (
                        self.current_predicted_keystream.copy()
                    )

                self._add_to_tabu(best_move)

            self.iteration += 1

            logger.debug(
                f"Iteration {self.iteration} completed: "
                f"current_fitness={self.current_fitness}, "
                f"best_fitness={self.best_fitness}"
            )

            # MODIFICADO: Devolver el estado ANTERIOR para visualización
            return {
                "iteration": self.iteration,
                "current_fitness": self.current_fitness,
                "best_fitness": self.best_fitness,
                "tabu_size": len(self.tabu_deque),
                "move_accepted": best_move,
                "best_candidate": self.best_candidate.copy(),
                "current_candidate": self.current_candidate.copy(),  # Estado NUEVO (post-swap)
                "display_candidate": previous_candidate,  # Estado VIEJO (pre-swap) para visualización
                "target_state": (
                    self.target_state.copy() if self.target_state is not None else None
                ),
                "predicted_keystream": self.current_predicted_keystream.copy(),
                "best_predicted_keystream": self.best_predicted_keystream.copy(),
                "target_keystream": self.target_keystream.copy(),
                "current_swap": self.current_swap,
            }

    def run(self, max_iterations=1000, callback=None):
        """
        Run Tabu Search for multiple iterations in background thread
        """

        def _run_loop():
            self.running = True
            for _ in range(max_iterations):
                if not self.running:
                    break

                stats = self.step()

                if callback:
                    callback(stats)

                if self.best_fitness == self.keystream_length:
                    break

                time.sleep(0.001)

            self.running = False

        self.thread = threading.Thread(target=_run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the running search"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def get_current_state(self):
        """
        Get current state for visualization
        """
        with self.lock:
            return {
                "candidate": self.current_candidate.copy(),
                "best_candidate": self.best_candidate.copy(),
                "fitness": self.current_fitness,
                "best_fitness": self.best_fitness,
                "iteration": self.iteration,
                "tabu_size": len(self.tabu_deque),
                "target_state": (
                    self.target_state.copy() if self.target_state is not None else None
                ),
                "predicted_keystream": self.current_predicted_keystream.copy(),
                "target_keystream": self.target_keystream.copy(),
            }
