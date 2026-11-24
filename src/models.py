"""Modelos reais SISO: coeficientes em potências decrescentes de s.

NumPy fornece apenas operações matemáticas e o solucionador geral de raízes.
Nenhum algoritmo deste núcleo chama SciPy ou python-control.
"""
from dataclasses import dataclass
import numpy as np


def polynomial(values):
    a = np.asarray(values, dtype=float)
    if a.ndim != 1 or len(a) == 0 or not np.all(np.isfinite(a)):
        raise ValueError("Coeficientes devem formar um vetor real finito não vazio.")
    nz = np.flatnonzero(a)
    return a[nz[0]:].copy() if len(nz) else np.array([0.0])


@dataclass(frozen=True)
class TransferFunction:
    numerator: np.ndarray
    denominator: np.ndarray
    delay: float = 0.0
    name: str = ""

    def __post_init__(self):
        num, den = polynomial(self.numerator), polynomial(self.denominator)
        if den[0] == 0:
            raise ValueError("Denominador nulo.")
        if not np.isfinite(self.delay) or self.delay < 0:
            raise ValueError("O atraso deve ser finito e não negativo.")
        num, den = num / den[0], den / den[0]
        num.setflags(write=False)
        den.setflags(write=False)
        object.__setattr__(self, "numerator", num)
        object.__setattr__(self, "denominator", den)

    @property
    def poles(self):
        return np.roots(self.denominator)

    @property
    def zeros(self):
        return np.roots(self.numerator) if np.any(self.numerator) else np.array([])

    def evaluate(self, s, gain=1.0, include_delay=True):
        if not np.isfinite(gain):
            raise ValueError("Ganho deve ser finito.")
        s = np.asarray(s, dtype=complex)
        response = gain * np.polyval(self.numerator, s) / np.polyval(self.denominator, s)
        if include_delay and self.delay:
            response = response * np.exp(-self.delay * s)
        return response

    def frequency_response(self, omega, gain=1.0):
        return self.evaluate(1j * np.asarray(omega), gain)

    def characteristic(self, gain=1.0):
        """D(s)+K N(s), realimentação negativa unitária, sem atraso."""
        if self.delay:
            raise ValueError("Com atraso, a equação é transcendental; use Padé explicitamente.")
        if not np.isfinite(gain):
            raise ValueError("Ganho deve ser finito.")
        return polynomial(np.polyadd(self.denominator, gain * self.numerator))

    def pade(self, order=3):
        """Aproximação [n/n] própria, por recorrência dos coeficientes."""
        if not isinstance(order, int) or not 1 <= order <= 12:
            raise ValueError("Ordem de Padé deve ser inteira entre 1 e 12.")
        if self.delay == 0:
            return self
        c = [1.0]
        for k in range(1, order + 1):
            c.append(c[-1] * (order-k+1) * self.delay / (k*(2*order-k+1)))
        den = np.array(c)[::-1]
        num = (np.array(c) * (-1.0)**np.arange(order+1))[::-1]
        return TransferFunction(np.convolve(self.numerator, num),
                                np.convolve(self.denominator, den),
                                name=f"{self.name} — Padé {order}")


def benchmark_models(delay=0.5):
    return {
        "A": TransferFunction([1], [1, 6, 11, 6], name="A — padrão"),
        "B": TransferFunction([1], [1, 4, 1, -6], name="B — instável em malha aberta"),
        "C": TransferFunction([-1, 1], [1, 6, 11, 6], name="C — fase não mínima"),
        "D": TransferFunction([1], [0.5, 1.5, 1], delay, "D — atraso de transporte"),
    }
