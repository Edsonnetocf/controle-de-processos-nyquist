"""Demonstração reprodutível do núcleo; não executa o futuro simulador PID."""
import argparse
import json
import platform
from pathlib import Path
import numpy as np
from src.models import benchmark_models
from src.nyquist import nyquist
from src.routh import routh
from src.frequency import bode, margins
from src.root_locus import root_locus


STATUS = {'stable': 'estável', 'unstable': 'instável',
          'boundary': 'fronteira — verificar', 'inconclusive': 'inconclusivo'}


def analyze_models(output, graphs=True):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    models = benchmark_models()
    gains = {'A': 10.0, 'B': 8.0, 'C': 4.0, 'D': 2.0}
    report = {'stage': 'Núcleo e testes matemáticos — sem PID ou benchmarking de escalabilidade',
              'python': platform.python_version(), 'numpy': np.__version__,
              'feedback': 'negativa unitária', 'models': {}}
    if graphs:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        report['matplotlib'] = matplotlib.__version__
        plt.rcParams.update({'font.size': 10, 'axes.grid': True, 'figure.dpi': 120})
    for key, model in models.items():
        gain = gains[key]
        nyq = nyquist(model, gain)
        margin = margins(model, gain)
        rational = model.pade(3) if model.delay else model
        r = routh(rational.characteristic(gain))
        item = {'gain': gain, 'delay_s': model.delay,
                'numerator': model.numerator.tolist(), 'denominator': model.denominator.tolist(),
                'nyquist': {'P': nyq.open_loop_unstable, 'N_clockwise': nyq.clockwise_encirclements,
                            'Z': nyq.closed_loop_unstable, 'status': nyq.status,
                            'converged': nyq.converged, 'min_critical_distance': nyq.min_critical_distance,
                            'nodes': len(nyq.contour), 'radius': nyq.radius},
                'routh': {'status': r.status, 'rhp_poles': r.right_half_plane_poles,
                          'approximation': 'Padé [3/3]' if model.delay else None},
                'margins': {'gain_margin_factor': margin.gain_margin,
                            'phase_margin_deg': margin.phase_margin_deg,
                            'gain_crossovers_rad_s': margin.gain_crossovers.tolist(),
                            'phase_crossovers_rad_s': margin.phase_crossovers.tolist(),
                            'all_gain_margin_factors': margin.gain_margins.tolist(),
                            'all_phase_margin_deg': margin.phase_margins_deg.tolist(),
                            'search_rad_s': [margin.omega_min, margin.omega_max]}}
        report['models'][key] = item
        np.savetxt(output/f'routh_{key}.csv', r.table, delimiter=',',
                   header=f'Linhas em potências decrescentes; escalonamento positivo; {item["routh"]["approximation"] or "sem aproximação"}',
                   encoding='utf-8')
        if graphs:
            frequency = bode(model, gain=gain)
            locus = root_locus(rational, np.r_[0, np.geomspace(1e-3, 150, 500)])
            fig, ax = plt.subplots(2, 2, figsize=(12, 8), layout='constrained')
            # Diagrama de frequência; a classificação usa o contorno completo.
            response = model.frequency_response(frequency.omega, gain)
            ax[0, 0].plot(response.real, response.imag, color='#006d77', label='ω > 0')
            ax[0, 0].plot(response.real, -response.imag, '--', color='#83c5be', label='ω < 0')
            ax[0, 0].plot(-1, 0, 'rx', ms=9, mew=2, label='Ponto crítico')
            ax[0, 0].set(title=f'Nyquist: P={nyq.open_loop_unstable}, N={nyq.clockwise_encirclements}, Z={nyq.closed_loop_unstable}',
                          xlabel='Parte real', ylabel='Parte imaginária')
            ax[0, 0].legend(fontsize=8)
            ax[0, 1].semilogx(frequency.omega, frequency.magnitude_db, color='#006d77')
            ax[0, 1].axhline(0, color='gray', ls='--')
            ax[0, 1].set(title='Bode — magnitude', xlabel='ω (rad/s)', ylabel='Magnitude (dB)')
            ax[1, 0].semilogx(frequency.omega, frequency.phase_deg, color='#006d77')
            ax[1, 0].axhline(-180, color='gray', ls='--')
            ax[1, 0].set(title='Bode — fase contínua', xlabel='ω (rad/s)', ylabel='Fase (graus)')
            # Limite visual da fase; todos os dados permanecem no CSV.
            if model.delay:
                ax[1, 0].set_ylim(-720, 0)
            for branch in locus.roots.T:
                ax[1, 1].plot(branch.real, branch.imag, lw=1)
            ax[1, 1].scatter(rational.poles.real, rational.poles.imag, marker='x', color='black', label='Polos')
            if len(rational.zeros):
                ax[1, 1].scatter(rational.zeros.real, rational.zeros.imag, marker='o', facecolors='none', edgecolors='black', label='Zeros')
            ax[1, 1].axvline(0, color='gray', ls='--')
            ax[1, 1].set(title='Lugar das raízes'+(' — Padé [3/3]' if model.delay else ''),
                          xlabel='Parte real (s⁻¹)', ylabel='Parte imaginária (rad/s)')
            ax[1, 1].legend(fontsize=8)
            fig.suptitle(f'{model.name} | K={gain:g} | τ={model.delay:g} s | {STATUS[nyq.status]}', fontsize=14)
            fig.savefig(output/f'sistema_{key}.png')
            plt.close(fig)
            np.savetxt(output/f'bode_{key}.csv', np.c_[frequency.omega, frequency.magnitude_db, frequency.phase_deg],
                       delimiter=',', header='omega_rad_s,magnitude_db,phase_deg')
            np.savetxt(output/f'lugar_raizes_{key}.csv',
                       np.c_[locus.gains, locus.roots.real, locus.roots.imag], delimiter=',',
                       header='K,partes reais dos ramos,partes imaginarias dos ramos')
        print(f'{key}: Nyquist {STATUS[nyq.status]}, P={nyq.open_loop_unstable}, '
              f'N={nyq.clockwise_encirclements}, Z={nyq.closed_loop_unstable}; '
              f'MG={margin.gain_margin}; MF={margin.phase_margin_deg}')
    (output/'analise_nucleo.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida', default='resultados/nucleo')
    parser.add_argument('--sem-graficos', action='store_true')
    args = parser.parse_args()
    analyze_models(args.saida, not args.sem_graficos)
