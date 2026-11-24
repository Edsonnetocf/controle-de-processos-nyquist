"""Nyquist com contorno fechado horário no semiplano direito.

Convenção do enunciado: N horário positivo e Z = N + P. O contorno
inclui o arco externo e desvios à direita de polos no eixo imaginário.
"""
from dataclasses import dataclass
import numpy as np


class CriticalPointError(ValueError):
    pass


def _segment_distances(values):
    delta = np.roll(values, -1)-values
    denominator = abs(delta)**2
    t = np.divide(-np.real(values*np.conj(delta)), denominator,
                  out=np.zeros(len(values)), where=denominator > 0)
    return abs(values+np.clip(t, 0, 1)*delta)


def winding_number(curve, center=-1.0, critical_tolerance=1e-7):
    """Número horário assinado de um polígono fechado, incluindo a aresta final."""
    values = np.asarray(curve, dtype=complex)-center
    if values.ndim != 1 or len(values) < 3 or not np.all(np.isfinite(values)):
        raise ValueError("Curva deve conter ao menos três pontos complexos finitos.")
    distance = float(min(_segment_distances(values)))
    if distance <= critical_tolerance:
        raise CriticalPointError("Curva passa pelo ponto crítico ou está muito próxima dele.")
    increments = np.angle(np.roll(values, -1)/values)
    raw = -float(np.sum(increments)/(2*np.pi))
    if abs(raw-round(raw)) > 1e-6:
        raise ArithmeticError("Contagem não inteira; contorno inadequado.")
    return int(round(raw)), raw, distance


@dataclass
class NyquistResult:
    open_loop_unstable: int
    clockwise_encirclements: int | None
    closed_loop_unstable: int | None
    status: str
    converged: bool
    min_critical_distance: float
    radius: float
    indent_radius: float
    contour: np.ndarray
    response: np.ndarray
    message: str


def outer_loop_bound(model, gain, radius):
    """Majorante de |K G(s)| para Re(s)>=0, |s|>=R, com atraso exato.

    Usa desigualdades triangulares divididas por R^n. Quando menor que 1,
    1+K G(s) não pode se anular fora do disco. A expressão diminui com R
    para plantas estritamente próprias; |exp(-tau*s)| <= 1 no semiplano.
    """
    n, m = len(model.denominator)-1, len(model.numerator)-1
    lower = 1-sum(abs(c)*radius**(-i) for i, c in enumerate(model.denominator[1:], 1))
    if lower <= 0:
        return float('inf')
    upper = sum(abs(gain)*abs(c)*radius**(-(n-m+i)) for i, c in enumerate(model.numerator))
    return float(upper/lower)


def _indent_loop_lower_bound(model, gain, center, radius):
    """Limite inferior de |L| no círculo: Rouché protege os desvios."""
    lower = abs(gain)*abs(model.numerator[0])*np.exp(-model.delay*radius)
    for zero in model.zeros:
        lower *= max(0.0, abs(center-zero)-radius)
    upper = np.prod([abs(center-pole)+radius for pole in model.poles])
    return float(lower/upper) if upper else float('inf')


def nyquist_contour(model, radius, indent_radius, points=2500):
    axis = model.poles[abs(model.poles.real) < 1e-9]
    centers = []
    for value in sorted(axis.imag):
        if abs(value) < radius and (not centers or abs(value-centers[-1]) > 1e-8):
            centers.append(float(value))
    if centers and (abs(centers[0])+indent_radius >= radius or
                    abs(centers[-1])+indent_radius >= radius):
        raise ValueError("Raio externo não contém os desvios.")
    if len(centers) > 1 and np.min(np.diff(centers)) <= 2*indent_radius:
        raise ValueError("Desvios de polos se sobrepõem; reduza o raio de desvio.")
    floor = min(indent_radius*0.01, radius*1e-8)
    positive = np.geomspace(max(floor, 1e-14), radius, points//2)
    grid = np.r_[-positive[::-1], 0.0, positive]
    parts = []
    start = -radius
    for center in centers:
        end = center-indent_radius
        samples = np.r_[start, grid[(grid > start) & (grid < end)], end]
        parts.extend([1j*samples, 1j*center + indent_radius*np.exp(1j*np.linspace(-np.pi/2, np.pi/2, 160))])
        start = center+indent_radius
    samples = np.r_[start, grid[(grid > start) & (grid < radius)], radius]
    parts.extend([1j*samples, radius*np.exp(1j*np.linspace(np.pi/2, -np.pi/2, 400))])
    result = np.concatenate(parts)
    # Remover pontos consecutivos repetidos e o último, que repete o primeiro.
    result = result[np.r_[True, abs(np.diff(result)) > 1e-14]]
    if abs(result[-1]-result[0]) < 1e-10:
        result = result[:-1]
    return result


def _refine(model, gain, contour, critical_tolerance):
    for _ in range(28):
        following = np.roll(contour, -1)
        mid = (contour+following)/2
        values = 1+model.evaluate(contour, gain)
        middle = 1+model.evaluate(mid, gain)
        after = np.roll(values, -1)
        if min(abs(values)) <= critical_tolerance or min(abs(middle)) <= critical_tolerance:
            return contour, False, True
        scale = np.maximum(np.minimum(abs(values), np.minimum(abs(after), abs(middle))), critical_tolerance)
        error = abs(middle-(values+after)/2)
        angle = np.maximum(abs(np.angle(middle/values)), abs(np.angle(after/middle)))
        refine = (error > 0.03*scale) | (angle > np.pi/4)
        if model.delay:
            large_loop = np.maximum(abs(values-1), np.maximum(abs(after-1), abs(middle-1))) > 0.2
            refine |= large_loop & (abs(following-contour)*model.delay > 0.25)
        if not np.any(refine):
            return contour, True, False
        if len(contour)+int(sum(refine)) > 150000:
            return contour, False, False
        expanded = np.empty(len(contour)+int(sum(refine)), dtype=complex)
        offsets = np.arange(len(contour))+np.r_[0, np.cumsum(refine[:-1])]
        expanded[offsets] = contour
        expanded[offsets[refine]+1] = mid[refine]
        contour = expanded
    return contour, False, False


def nyquist(model, gain=1.0, points=2500, radius=None,
            indent_radius=1e-4, critical_tolerance=1e-7):
    if not np.isfinite(gain) or gain <= 0:
        raise ValueError("Nyquist exige ganho positivo.")
    if len(model.numerator) >= len(model.denominator):
        raise ValueError("Esta implementação exige função estritamente própria.")
    if points < 100 or indent_radius <= 0 or critical_tolerance <= 0:
        raise ValueError("Malha ou tolerâncias inválidas.")
    poles, zeros = model.poles, model.zeros
    if any(abs(p-z) < 1e-8 for p in poles for z in zeros):
        raise ValueError("Cancelamento polo-zero: analise a realização interna antes de usar Nyquist.")
    scale = max(1.0, float(max(abs(np.r_[poles, zeros]), default=1.0)))
    radius = float(radius) if radius is not None else 100*scale
    if radius <= max(abs(poles), default=0)*1.01 or not np.isfinite(radius):
        raise ValueError("Raio externo deve conter todos os polos.")
    for _ in range(80):
        if outer_loop_bound(model, gain, radius) < 0.1:
            break
        radius *= 2
    else:
        raise ArithmeticError("Não foi possível certificar o truncamento do contorno.")
    p = int(sum(poles.real > 1e-9))
    near_axis = (abs(poles.real) < 1e-9) & (poles.real != 0)
    if np.any(near_axis):
        return NyquistResult(p, None, None, "inconclusive", False, 0.0,
                             radius, indent_radius, np.array([], dtype=complex),
                             np.array([], dtype=complex),
                             "Polos quase no eixo: precisão insuficiente para distinguir o semiplano.")
    axis = poles[abs(poles.real) < 1e-9]
    if len(axis):
        while min(_indent_loop_lower_bound(model, gain, pole, indent_radius) for pole in axis) <= 10:
            indent_radius /= 10
            if indent_radius < 1e-12*scale:
                return NyquistResult(p, None, None, "inconclusive", False, 0.0,
                                     radius, indent_radius, np.array([], dtype=complex),
                                     np.array([], dtype=complex),
                                     "Desvio necessário é pequeno demais para certificação numérica.")
    counts = []
    for run in range(2):
        r, indent = radius*(2**run), indent_radius/(2**run)
        contour = nyquist_contour(model, r, indent, points*(run+1))
        contour, refined, critical = _refine(model, gain, contour, critical_tolerance)
        response = model.evaluate(contour, gain)
        distance = float(min(_segment_distances(1+response)))
        if critical or distance <= critical_tolerance:
            return NyquistResult(p, None, None, "boundary", False, distance, r, indent,
                                 contour, response, "Proximidade do ponto crítico; estabilidade não certificada.")
        if not refined:
            return NyquistResult(p, None, None, "inconclusive", False, distance, r, indent,
                                 contour, response, "Refinamento atingiu o limite; não há classificação confiável.")
        count, _, distance = winding_number(response, critical_tolerance=critical_tolerance)
        counts.append(count)
    z = counts[-1]+p
    converged = counts[0] == counts[1] and z >= 0
    status = ("stable" if z == 0 else "unstable") if converged else "inconclusive"
    return NyquistResult(p, counts[-1], z if converged else None, status,
                         converged, distance, r, indent, contour, response,
                         "Contagem concordante após duplicar raio/malha e reduzir desvio."
                         if converged else "Contagens inconsistentes; ampliar análise.")
