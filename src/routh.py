"""Tabela de Routh com escalonamento positivo, pivô epsilon e linha auxiliar."""
from dataclasses import dataclass
import numpy as np
from .models import polynomial


@dataclass
class RouthResult:
    table: np.ndarray
    right_half_plane_poles: int
    status: str
    epsilon_rows: list
    auxiliary_rows: list
    epsilon: float


def routh(coefficients, epsilon=1e-9, zero_tolerance=1e-12):
    """Conta trocas de sinal. 'boundary' não afirma estabilidade marginal.

    Cada linha é dividida por uma constante positiva. Zero na primeira
    coluna recebe epsilon positivo. Uma linha nula recebe a derivada do
    polinômio auxiliar da linha anterior. Em casos sensíveis, repetir com
    epsilons diferentes e conferir referências independentes.
    """
    if not 0 < zero_tolerance < epsilon < 0.01:
        raise ValueError("Exigir 0 < tolerância < epsilon < 0,01.")
    a = polynomial(coefficients).astype(np.longdouble)
    if a[0] == 0:
        raise ValueError("Polinômio nulo não possui classificação de Routh.")
    if a[0] < 0:
        a = -a
    a /= np.max(abs(a))
    n = len(a)-1
    if n == 0:
        return RouthResult(np.array([[1.0]]), 0, "stable", [], [], epsilon)
    width = (n+2)//2
    table = np.zeros((n+1, width), dtype=np.longdouble)
    table[0, :len(a[::2])] = a[::2]
    table[1, :len(a[1::2])] = a[1::2]
    pivots, auxiliary = [], []

    def prepare(row):
        scale = np.max(np.abs(table[row]))
        if scale <= zero_tolerance:
            if row == 0:
                raise ArithmeticError("Primeira linha nula.")
            auxiliary.append(row)
            previous_power = n-row+1
            for col in range(width):
                power = previous_power-2*col
                if power > 0:
                    table[row, col] = power*table[row-1, col]
            scale = np.max(np.abs(table[row]))
            if scale:
                table[row] /= scale
        else:
            table[row] /= scale
        if abs(table[row, 0]) <= zero_tolerance:
            pivots.append(row)
            table[row, 0] = epsilon

    prepare(0)
    prepare(1)
    for row in range(2, n+1):
        for col in range(width-1):
            table[row, col] = (table[row-1, 0]*table[row-2, col+1]
                               - table[row-2, 0]*table[row-1, col+1])/table[row-1, 0]
        prepare(row)
    first = table[:, 0]
    changes = int(np.sum(np.sign(first[1:]) != np.sign(first[:-1])))
    status = "unstable" if changes else ("boundary" if auxiliary else "stable")
    return RouthResult(np.asarray(table, dtype=float), changes, status,
                       pivots, auxiliary, epsilon)
