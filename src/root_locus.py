"""Lugar das raízes e associação global de ramos sem bibliotecas de controle."""
from dataclasses import dataclass
import numpy as np


def minimum_cost_assignment(cost):
    """Algoritmo húngaro O(n³), devolve coluna associada a cada linha."""
    cost = np.asarray(cost, dtype=float)
    if cost.ndim != 2 or cost.shape[0] != cost.shape[1] or not np.all(np.isfinite(cost)):
        raise ValueError("Matriz de custo deve ser quadrada e finita.")
    n = len(cost)
    u, v = np.zeros(n+1), np.zeros(n+1)
    p, way = np.zeros(n+1, dtype=int), np.zeros(n+1, dtype=int)
    for row in range(1, n+1):
        p[0] = row
        col0 = 0
        best = np.full(n+1, np.inf)
        used = np.zeros(n+1, dtype=bool)
        while True:
            used[col0] = True
            row0 = p[col0]
            delta, col1 = np.inf, 0
            for col in range(1, n+1):
                if not used[col]:
                    current = cost[row0-1, col-1]-u[row0]-v[col]
                    if current < best[col]:
                        best[col], way[col] = current, col0
                    if best[col] < delta:
                        delta, col1 = best[col], col
            for col in range(n+1):
                if used[col]:
                    u[p[col]] += delta
                    v[col] -= delta
                else:
                    best[col] -= delta
            col0 = col1
            if p[col0] == 0:
                break
        while col0:
            col1 = way[col0]
            p[col0] = p[col1]
            col0 = col1
    assignment = np.empty(n, dtype=int)
    for col in range(1, n+1):
        assignment[p[col]-1] = col-1
    return assignment


@dataclass
class RootLocusResult:
    gains: np.ndarray
    roots: np.ndarray


def root_locus(model, gains):
    if model.delay:
        raise ValueError("Lugar das raízes exige aproximação racional explícita do atraso.")
    if len(model.numerator) >= len(model.denominator):
        raise ValueError("Este traçador exige função estritamente própria.")
    gains = np.asarray(gains, dtype=float)
    if gains.ndim != 1 or len(gains) == 0 or not np.all(np.isfinite(gains)) or np.any(gains < 0):
        raise ValueError("Ganhos devem formar vetor finito, não negativo e não vazio.")
    if np.any(np.diff(gains) < 0):
        raise ValueError("Ganhos devem estar em ordem crescente.")
    branches = []
    for gain in gains:
        roots = np.asarray(np.roots(model.characteristic(gain)), dtype=complex)
        if not branches:
            roots = roots[np.lexsort((roots.imag, roots.real))]
        else:
            cost = abs(branches[-1][:, None]-roots[None, :])**2
            roots = roots[minimum_cost_assignment(cost)]
        branches.append(roots)
    return RootLocusResult(gains, np.asarray(branches))
