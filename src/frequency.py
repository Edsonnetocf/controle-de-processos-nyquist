"""Bode e margens por busca própria de cruzamentos e bisseção logarítmica."""
from dataclasses import dataclass
import numpy as np


@dataclass
class BodeResult:
    omega: np.ndarray
    magnitude_db: np.ndarray
    phase_deg: np.ndarray


@dataclass
class MarginResult:
    gain_crossovers: np.ndarray
    phase_margins_deg: np.ndarray
    phase_crossovers: np.ndarray
    gain_margins: np.ndarray
    omega_min: float
    omega_max: float

    @property
    def phase_margin_deg(self):
        a = self.phase_margins_deg
        return float(a[np.argmin(abs(a))]) if len(a) else None

    @property
    def gain_margin(self):
        a = self.gain_margins
        return float(a[np.argmin(abs(np.log(a)))]) if len(a) else None


def frequency_grid(model, points=5000):
    scales = abs(np.r_[model.poles, model.zeros])
    scales = scales[scales > 1e-10]
    low = min(1.0, float(min(scales))) if len(scales) else 1.0
    high = max(1.0, float(max(scales))) if len(scales) else 1.0
    return np.geomspace(low*1e-5, high*1e3, points)


def bode(model, omega=None, gain=1.0):
    if not np.isfinite(gain) or gain <= 0:
        raise ValueError("Bode e margens exigem ganho positivo.")
    w = frequency_grid(model) if omega is None else np.asarray(omega, dtype=float)
    if w.ndim != 1 or len(w) < 2 or not np.all(np.isfinite(w)) or np.any(w <= 0) or np.any(np.diff(w) <= 0):
        raise ValueError("Frequências devem ser positivas, finitas e estritamente crescentes.")
    rational = model.evaluate(1j*w, gain, include_delay=False)
    if np.any(abs(rational) == 0) or not np.all(np.isfinite(rational)):
        raise ValueError("Bode não definido em um zero ou polo sobre a malha fornecida.")
    # Desembrulhar antes de subtrair o atraso evita aliasing artificial da fase.
    phase = np.unwrap(np.angle(rational))-w*model.delay
    return BodeResult(w, 20*np.log10(abs(rational)), np.degrees(phase))


def _bisect_log(function, a, b, tolerance=1e-12):
    fa, fb = function(a), function(b)
    if abs(fa) < tolerance:
        return a
    if abs(fb) < tolerance:
        return b
    if fa*fb > 0:
        raise ValueError("Intervalo sem mudança de sinal.")
    for _ in range(90):
        mid = np.sqrt(a*b)
        fm = function(mid)
        if abs(fm) < tolerance or b/a-1 < tolerance:
            return mid
        if fa*fm <= 0:
            b = mid
        else:
            a, fa = mid, fm
    return mid


def _unique(values):
    result = []
    for value in sorted(values):
        if not result or abs(np.log(value/result[-1])) > 1e-7:
            result.append(value)
    return np.asarray(result)


def margins(model, gain=1.0, omega=None):
    """Reporta cruzamentos encontrados no intervalo informado.

    Não encontrar cruzamento não prova margem infinita. A busca por mudança
    de sinal pode perder contatos tangenciais; aumentar a malha não elimina
    essa limitação. Margens isoladas não certificam estabilidade com P > 0.
    """
    response = bode(model, omega, gain)
    w, db = response.omega, response.magnitude_db
    rational_phase = np.radians(response.phase_deg)+w*model.delay

    def phase_at(value):
        ref = rational_phase[0] if value == 0 else np.interp(np.log(value), np.log(w), rational_phase)
        angle = float(np.angle(model.evaluate(1j*value, gain, include_delay=False)))
        angle += 2*np.pi*round((ref-angle)/(2*np.pi))
        return angle-value*model.delay

    def log_magnitude(value):
        return float(np.log(abs(model.frequency_response(value, gain))))

    gain_cross = []
    for i in np.flatnonzero(db[:-1]*db[1:] <= 0):
        gain_cross.append(_bisect_log(log_magnitude, w[i], w[i+1]))
    gain_cross = _unique(gain_cross)
    dc = complex(model.evaluate(0, gain)) if model.denominator[-1] != 0 else None
    if dc is not None and abs(abs(dc)-1) < 1e-12:
        gain_cross = np.r_[0.0, gain_cross]
    pm = np.array([(np.degrees(phase_at(value))+360) % 360-180 for value in gain_cross])

    phase = np.radians(response.phase_deg)
    phase_cross = []
    for i in range(len(w)-1):
        low, high = sorted((phase[i], phase[i+1]))
        first = int(np.ceil((low/np.pi-1)/2))
        last = int(np.floor((high/np.pi-1)/2))
        for m in range(first, last+1):
            target = (2*m+1)*np.pi
            phase_cross.append(_bisect_log(lambda x: phase_at(x)-target, w[i], w[i+1]))
    phase_cross = _unique(phase_cross)
    if dc is not None and dc.real < 0 and abs(dc.imag) < 1e-12:
        phase_cross = np.r_[0.0, phase_cross]
    gm = np.array([1/abs(model.frequency_response(value, gain)) for value in phase_cross])
    return MarginResult(gain_cross, pm, phase_cross, gm, float(w[0]), float(w[-1]))
