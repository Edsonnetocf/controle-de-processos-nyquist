"""PID digital e planta D com retenção de ordem zero, implementados com NumPy.

Planta: x'= -x+u_atrasado, y'=2(x-y). Integração exata sob entrada
constante entre amostras. Integral trapezoidal e derivada filtrada na medição.
Não há saturação: os experimentos investigam a estabilidade do modelo linear.
"""
from collections import deque
from dataclasses import dataclass, asdict
import numpy as np
from .models import TransferFunction
from .frequency import margins, _bisect_log


@dataclass(frozen=True)
class PIDConfig:
    kp: float = 2.0
    ki: float = 1.0
    kd: float = 0.2
    tf: float = 0.05
    sample_time: float = 0.01

    def __post_init__(self):
        values = [self.kp, self.ki, self.kd, self.tf, self.sample_time]
        if not np.all(np.isfinite(values)) or min(values[:3]) < 0 or self.kp <= 0 or self.ki <= 0:
            raise ValueError('Exigir Kp e Ki positivos e Kd não negativo, todos finitos.')
        if self.tf <= 0 or not 0 < self.sample_time <= 0.1:
            raise ValueError('Exigir Tf positivo e período entre 0 e 0,1 s.')


def continuous_loop(config, delay=0.0):
    """C(s)G_D(s), C=Kp+Ki/s+Kd*s/(Tf*s+1), referência contínua."""
    c = config
    return TransferFunction([c.kp*c.tf+c.kd, c.kp+c.ki*c.tf, c.ki],
                            np.convolve([c.tf, 1, 0], [0.5, 1.5, 1]),
                            delay, 'PID e planta D')


def plant_zoh_coefficients(sample_time):
    a = np.exp(-sample_time)
    b = np.exp(-2*sample_time)
    return (1-a)**2*np.array([1, a]), np.array([1, -(a+b), a*b])


def discrete_loop_coefficients(config):
    c, ts = config, config.sample_time
    di, dd = np.array([1, -1]), np.array([c.tf+ts, -c.tf])
    den_c = np.convolve(di, dd)
    num_c = np.polyadd(c.kp*den_c, c.ki*ts/2*np.convolve([1, 1], dd))
    num_c = np.polyadd(num_c, c.kd*np.convolve([1, -1], di))
    num_p, den_p = plant_zoh_coefficients(ts)
    return np.convolve(num_c, num_p), np.convolve(den_c, den_p)


def delay_limits(config):
    """Primeiro atraso crítico, para o PID configurado e base estável.

    Previsão contínua e previsão digital por resposta em z. O limite digital
    pressupõe atraso de fase puro; a simulação usa número inteiro de amostras.
    Todos os cruzamentos de ganho transversais encontrados são considerados.
    """
    model = continuous_loop(config)
    if np.any(np.roots(model.characteristic()).real >= -1e-9):
        raise ValueError('O PID sem atraso não é estritamente estável no modelo contínuo.')
    result = margins(model)
    continuous = [np.radians(pm)/wc for pm, wc in zip(result.phase_margins_deg, result.gain_crossovers) if pm > 0]
    num, den = discrete_loop_coefficients(config)
    if np.any(abs(np.roots(np.polyadd(den, num))) >= 1):
        raise ValueError('O PID sem atraso não é estritamente estável no modelo digital.')
    ts = config.sample_time
    w = np.geomspace(1e-4, np.pi/ts*(1-1e-8), 8000)
    z = np.exp(1j*w*ts)
    loop = np.polyval(num, z)/np.polyval(den, z)
    phase = np.unwrap(np.angle(loop))
    db = np.log(abs(loop))
    critical = []
    crossovers = []
    for i in np.flatnonzero(db[:-1]*db[1:] < 0):
        def magnitude(value):
            zv = np.exp(1j*value*ts)
            return float(np.log(abs(np.polyval(num, zv)/np.polyval(den, zv))))
        wc = _bisect_log(magnitude, w[i], w[i+1])
        zv = np.exp(1j*wc*ts)
        angle = np.angle(np.polyval(num, zv)/np.polyval(den, zv))
        ref = np.interp(np.log(wc), np.log(w), phase)
        angle += 2*np.pi*round((ref-angle)/(2*np.pi))
        available = (angle+np.pi) % (2*np.pi)
        if available > 1e-12:
            critical.append(float(available/wc))
            crossovers.append(float(wc))
    if not continuous or not critical:
        raise ValueError('Limite não encontrado; ampliar a análise de cruzamentos.')
    return {'continuous_s': float(min(continuous)), 'digital_s': min(critical),
            'digital_crossovers_rad_s': crossovers,
            'sample_time_s': ts, 'prediction_scope': 'modelo linear; atraso constante; base estável'}


@dataclass
class SimulationResult:
    time: np.ndarray
    output: np.ndarray
    command: np.ndarray
    delayed_command: np.ndarray
    requested_delay: float
    effective_delay: float
    delay_samples: int
    stopped_early: bool
    config: PIDConfig

    def metrics(self):
        error = 1-self.output
        tail = max(1, len(error)//5)
        settling = None
        outside = np.flatnonzero(abs(error) > 0.02)
        if len(outside) and outside[-1] < len(error)-1 and not self.stopped_early:
            settling = float(self.time[outside[-1]+1])
        return {'max_abs_output': float(max(abs(self.output))),
                'final_output': float(self.output[-1]),
                'tail_max_abs_error': float(max(abs(error[-tail:]))),
                'iae': float(np.trapezoid(abs(error), self.time)),
                'overshoot_percent': float(max(0, max(self.output)-1)*100),
                'settling_time_2pct_s_observed': settling,
                'requested_delay_s': self.requested_delay,
                'effective_delay_s': self.effective_delay,
                'delay_samples': self.delay_samples,
                'stopped_early': self.stopped_early,
                'duration_s': float(self.time[-1]), 'config': asdict(self.config)}


def simulate_pid(config=PIDConfig(), delay=0.0, duration=60.0, safety_limit=1e6):
    if not np.isfinite(delay) or delay < 0 or delay > 10:
        raise ValueError('Atraso deve estar entre 0 e 10 s.')
    if not np.isfinite(duration) or not 1 <= duration <= 300 or safety_limit <= 1:
        raise ValueError('Duração deve estar entre 1 e 300 s e limite maior que 1.')
    ts = config.sample_time
    steps = int(np.ceil(duration/ts))
    if steps > 300000:
        raise ValueError('A configuração excede 300 mil amostras.')
    delay_samples = int(np.floor(delay/ts+0.5))
    buffer = deque([0.0]*delay_samples)
    output, command, delayed = np.zeros(steps+1), np.zeros(steps+1), np.zeros(steps+1)
    x = integral = derivative = previous_error = previous_output = 0.0
    a, b = np.exp(-ts), np.exp(-2*ts)
    stopped = False
    for k in range(steps):
        y = output[k]
        error = 1-y
        integral += config.ki*ts/2*(error+previous_error)
        derivative = config.tf/(config.tf+ts)*derivative+(y-previous_output)/(config.tf+ts)
        u = config.kp*error+integral-config.kd*derivative
        applied = buffer.popleft() if delay_samples else u
        if delay_samples:
            buffer.append(u)
        command[k], delayed[k] = u, applied
        output[k+1] = b*y+2*(a-b)*x+(1-a)**2*applied
        x = a*x+(1-a)*applied
        previous_error, previous_output = error, y
        if max(abs(output[k+1]), abs(u), abs(x)) > safety_limit:
            steps = k+1
            stopped = True
            break
    command[steps] = command[steps-1]
    delayed[steps] = delayed[steps-1]
    return SimulationResult(np.arange(steps+1)*ts, output[:steps+1], command[:steps+1],
                            delayed[:steps+1], delay, delay_samples*ts, delay_samples, stopped, config)
