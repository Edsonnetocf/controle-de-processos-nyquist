"""Referências externas restritas à validação, fora do núcleo src/."""
import json
import warnings
from pathlib import Path
import numpy as np
import scipy
from scipy import signal
import control as ct
from src.models import benchmark_models, TransferFunction
from src.routh import routh
from src.nyquist import nyquist
from src.frequency import margins, frequency_grid
from src.root_locus import root_locus
from src.pid import PIDConfig, plant_zoh_coefficients, simulate_pid, discrete_loop_coefficients
from scipy.optimize import linear_sum_assignment


def root_error(actual, expected):
    cost = abs(np.asarray(actual)[:, None]-np.asarray(expected)[None, :])
    rows, cols = linear_sum_assignment(cost)
    return float(max(cost[rows, cols], default=0.0))


def run_validation(folder='resultados/validacao'):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    cases = []
    models = benchmark_models()
    for key, gains in {'A':[10,59,61], 'B':[5,8,11], 'C':[4,8,9], 'D':[2]}.items():
        original = models[key]
        model = original.pade(3) if original.delay else original
        for gain in gains:
            reference = ct.tf(gain*model.numerator, model.denominator)
            closed = ct.poles(ct.feedback(reference))
            rhp = int(sum(closed.real > 1e-8))
            own_n = nyquist(model, gain)
            own_r = routh(model.characteristic(gain))
            with warnings.catch_warnings(record=True) as captured:
                library_n = ct.nyquist_response(reference, omega=np.geomspace(1e-6, 1e5, 20000), warn_encirclements=True)
            m = margins(model, gain)
            gm, pm, _, _ = ct.margin(reference)
            gm_error = abs(m.gain_margin-gm) if m.gain_margin is not None and np.isfinite(gm) else None
            pm_error = abs(m.phase_margin_deg-pm) if m.phase_margin_deg is not None and np.isfinite(pm) else None
            absence_ok = (m.phase_margin_deg is None) == (not np.isfinite(pm))
            absence_ok &= (m.gain_margin is None) == (not np.isfinite(gm))
            w = np.geomspace(1e-3, 100, 1000)
            _, scipy_response = signal.freqs(gain*model.numerator, model.denominator, w)
            response_error = float(max(abs(model.frequency_response(w, gain)-scipy_response)/(1+abs(scipy_response))))
            k_values = np.array([0.0, gain/2, gain, gain*1.5])
            own_locus = root_locus(model, k_values)
            reference_locus = ct.root_locus_map(ct.tf(model.numerator, model.denominator), gains=k_values)
            locus_error = max(root_error(a,b) for a,b in zip(own_locus.roots, reference_locus.loci))
            passed = (own_n.closed_loop_unstable == own_r.right_half_plane_poles == rhp
                      and own_n.clockwise_encirclements == int(library_n.count)
                      and absence_ok and (gm_error is None or gm_error < 1e-6)
                      and (pm_error is None or pm_error < 1e-5)
                      and response_error < 1e-10 and locus_error < 1e-6)
            cases.append({'case':key, 'gain':gain, 'delay_treatment':'Padé [3/3]' if original.delay else 'racional',
                          'rhp_reference':rhp,'rhp_routh':own_r.right_half_plane_poles,
                          'rhp_nyquist':own_n.closed_loop_unstable,'N_reference':int(library_n.count),
                          'N_own':own_n.clockwise_encirclements,'gain_margin_abs_error':gm_error,
                          'phase_margin_abs_error_deg':pm_error,'absence_consistent':bool(absence_ok),
                          'frequency_normalized_error':response_error,'locus_max_abs_error':locus_error,
                          'reference_warnings':[str(item.message) for item in captured], 'passed':bool(passed)})
    # Atraso exato: referência analítica independente da aproximação de Padé.
    wc = np.sqrt((-1.25+np.sqrt(1.25**2+3))/0.5)
    tau_critical = (np.pi-np.arctan(wc)-np.arctan(0.5*wc))/wc
    exact_delay_cases = []
    for factor, expected in [(0.8,0),(1.2,2)]:
        plant = benchmark_models(delay=tau_critical*factor)['D']
        actual = nyquist(plant, 2)
        w = frequency_grid(plant, 20000)
        response = plant.frequency_response(w, 2)
        gm, pm, _, _ = ct.margin(abs(response), np.degrees(np.unwrap(np.angle(response))), w)
        own = margins(plant, 2, w)
        passed = actual.closed_loop_unstable == expected and abs(own.phase_margin_deg-pm) < 0.002 and abs(own.gain_margin-gm) < 0.002
        exact_delay_cases.append({'factor':factor,'tau_s':plant.delay,'analytic_tau_critical_s':tau_critical,
                                 'expected_rhp':expected,'computed_rhp':actual.closed_loop_unstable,
                                 'phase_margin_error_deg':abs(own.phase_margin_deg-pm),
                                 'gain_margin_error':abs(own.gain_margin-gm),'passed':bool(passed),
                                 'scope':'Contagem por limite analítico; margens por FRD amostrada, sem Padé.'})
    # Atualização exata da planta contra discretização ZOH de SciPy.
    discretization_errors = []
    for ts in (0.005,0.01,0.05):
        num, den = plant_zoh_coefficients(ts)
        a,b,c,d,_ = signal.cont2discrete((np.array([[-1.,0.],[2.,-2.]]), np.array([[1.],[0.]]),np.array([[0.,1.]]),np.array([[0.]])),ts)
        _, yref = signal.dlsim((a,b,c,d,ts), np.ones(1000))[:2]
        yown = signal.lfilter(np.r_[0,num],den,np.ones(1000))
        discretization_errors.append(float(max(abs(yown-yref[:,0]))))
    # PID: transferência digital externa com derivada na medição (2 graus de liberdade).
    cfg=PIDConfig()
    num_p,den_p=plant_zoh_coefficients(cfg.sample_time)
    num_l,den_l=discrete_loop_coefficients(cfg)
    di,dd=np.array([1,-1]),np.array([cfg.tf+cfg.sample_time,-cfg.tf])
    num_pi=np.polyadd(cfg.kp*np.convolve(di,dd),cfg.ki*cfg.sample_time/2*np.convolve([1,1],dd))
    reference_num=np.r_[0,np.convolve(num_pi,num_p)]
    reference_den=np.polyadd(den_l,num_l)
    own=simulate_pid(cfg,0,10)
    # Coeficientes de potência em z são alinhados pelo grau do denominador.
    reference_num=np.pad(reference_num,(len(reference_den)-len(reference_num),0))
    digital_reference=signal.lfilter(reference_num,reference_den,np.ones(len(own.time)))
    pid_error=float(max(abs(own.output-digital_reference)))
    report={'scipy':scipy.__version__,'python_control':ct.__version__,'cases':cases,
            'exact_delay_cases':exact_delay_cases,'plant_zoh_max_error':max(discretization_errors),
            'pid_time_series_max_error':pid_error,
            'all_passed':all(c['passed'] for c in cases+exact_delay_cases) and max(discretization_errors)<1e-9 and pid_error<1e-6,
            'limitations':'Bibliotecas de controle também usam NumPy em várias rotinas; referências analíticas complementam essa comparação.'}
    (folder/'validacao_cruzada.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return report


if __name__=='__main__':
    raise SystemExit(0 if run_validation()['all_passed'] else 1)
