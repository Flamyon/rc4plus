"""
Tabu Search State Recovery Attack - Z2 Configuration
Implements the exact parameters from Polak & Boryczka (2019) Experiment 2, Set Z2
"""

import numpy as np
import threading
import time
from collections import deque
import logging

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

    S_work = S.copy()
    i, j = 0, 0 
    keystream = np.zeros(length, dtype=np.uint8)

    n_bits = int(np.ceil(np.log2(N)))

    for step in range(length):
        try:
            i = (i + 1) % N
            j = (j + int(S_work[i])) % N  
            S_work[i], S_work[j] = S_work[j], S_work[i]

            t = (int(S_work[i]) + int(S_work[j])) % N 
            shift_right = max(1, n_bits // 3)  
            shift_left = max(1, n_bits - shift_right) 
            idx1 = ((int(i) >> shift_right) ^ (int(j) << shift_left)) % N
            idx2 = ((int(i) << shift_left) ^ (int(j) >> shift_right)) % N

            
            if idx1 >= N or idx2 >= N:
                logger.error(f"INDEX OUT OF BOUNDS! idx1={idx1}, idx2={idx2}, N={N}")
                raise IndexError(
                    f"Calculated index out of bounds: idx1={idx1}, idx2={idx2}, N={N}"
                )

            t_prime_val = (int(S_work[idx1]) + int(S_work[idx2])) % N
            xor_constant = (0xAA * N) // 256
            t_prime = (t_prime_val ^ xor_constant) % N

            t_double = (int(j) + int(S_work[j])) % N
            
            if N < 256:
                scale_factor = 256.0 / N
                val1 = (
                    int((S_work[t] * scale_factor + S_work[t_prime] * scale_factor))
                    & 0xFF
                )
                output = (val1 ^ int(S_work[t_double] * scale_factor)) & 0xFF
            else:
                val1 = (int(S_work[t]) + int(S_work[t_prime])) & 0xFF
                output = (val1 ^ int(S_work[t_double])) & 0xFF

            keystream[step] = output

        except Exception as e:
            logger.error(f"ERROR at step {step}: {e}", exc_info=True)
            logger.error(f"State at error: i={i}, j={j}, N={N}")
            logger.error(f"S_work min={S_work.min()}, max={S_work.max()}")
            raise

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

    if N not in [64, 128, 256]:
        raise ValueError(f"N must be 64, 128, or 256. Got: {N}")

    if N <= 256:
        dtype = np.uint8
    else:
        dtype = np.uint16

    target_state = np.arange(N, dtype=dtype)
    np.random.shuffle(target_state)


    try:
        target_keystream = rc4_plus_prga(target_state, length, N)
        logger.info("Keystream generation completed successfully")
        return target_state, target_keystream
    except Exception as e:
        logger.error(f"Failed to generate keystream: {e}", exc_info=True)
        raise


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

        if N not in [64, 128, 256]:
            raise ValueError(f"N must be 64, 128, or 256. Got: {N}")

        self.N = N
        self.target_keystream = np.array(target_keystream, dtype=np.uint8)
        self.keystream_length = len(target_keystream)

        self.target_state = target_state.copy() if target_state is not None else None
        self.total_swaps = (N * (N - 1)) // 2
        self.swaps_per_iteration = self.total_swaps // 2
        self.tabu_horizon = self.swaps_per_iteration

        self.all_swaps = np.array(
            [(i, j) for i in range(N) for j in range(i + 1, N)], dtype=np.int32
        )

        dtype = np.uint8 if N <= 256 else np.uint16
        self.current_candidate = np.arange(N, dtype=dtype)
        np.random.shuffle(self.current_candidate)

        self.best_candidate = self.current_candidate.copy()

        logger.info("Calculating initial fitness...")
        self.best_fitness = self._calculate_fitness(self.best_candidate)
        logger.info(f"Initial fitness: {self.best_fitness}/{self.keystream_length}")

        self.tabu_deque = deque(maxlen=self.tabu_horizon)
        self.tabu_set = set()

        self.iteration = 0
        self.current_fitness = self.best_fitness

        # Store current predicted keystream for visualization
        self.current_predicted_keystream = self._generate_keystream(
            self.current_candidate
        )

        self.best_predicted_keystream = self.current_predicted_keystream.copy()

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
        return rc4_plus_prga(S, self.keystream_length, self.N)

    def _calculate_fitness(self, candidate):
        """
        Z2 Fitness Function: Byte Fitness
        Counts exact matches between generated and target keystream.
        """
        try:
            candidate_keystream = self._generate_keystream(candidate)
            matches = np.sum(candidate_keystream == self.target_keystream)
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

    def run(self, max_iterations=1000, callback=None, delay=0.001):
        """
        Run Tabu Search for multiple iterations in background thread

        Args:
            max_iterations: Maximum number of iterations
            callback: Optional callback function for progress updates
            delay: Delay between iterations in seconds (0 for maximum speed)
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

                # Only sleep if delay > 0
                if delay > 0:
                    time.sleep(delay)

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
