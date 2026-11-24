"""Escalabilidade: CPU, tempo decorrido e condicionamento nas ordens 5/10/20."""
import csv
import json
import math
import os
import platform
from fractions import Fraction
from pathlib import Path
from time import perf_counter_ns, process_time_ns
import numpy as np
from src.models import TransferFunction
from src.routh import routh
from src.nyquist import nyquist
from src.frequency import margins
from src.root_locus import root_locus, minimum_cost_assignment


def exact_routh_count(coefficients):
    """Referência racional exata para o polinômio float64 fornecido.

    Esta referência não usa epsilon; rejeita pivô isolado nulo, ausente
    nas famílias de benchmark. Linhas nulas usam a derivada auxiliar.
    """
    a = [Fraction(float(value)) for value in coefficients]
    n, width = len(a)-1, (len(a)+1)//2
    rows = [[Fraction(0) for _ in range(width)] for _ in range(n+1)]
    rows[0][:len(a[::2])], rows[1][:len(a[1::2])] = a[::2], a[1::2]
    for i in range(1,n+1):
        if i >= 2:
            if not rows[i-1][0]:
                raise ArithmeticError('Referência exata encontrou pivô isolado nulo.')
            for j in range(width-1):
                rows[i][j]=(rows[i-1][0]*rows[i-2][j+1]-rows[i-2][0]*rows[i-1][j+1])/rows[i-1][0]
        if not any(rows[i]):
            power=n-i+1
            rows[i]=[rows[i-1][j]*max(power-2*j,0) for j in range(width)]
    signs=[1 if row[0]>0 else -1 if row[0]<0 else 0 for row in rows]
    if 0 in signs:
        raise ArithmeticError('Referência exata requer análise de limite neste caso.')
    return sum(signs[i]!=signs[i-1] for i in range(1,len(signs)))


def generated_polynomial(roots):
    a=[Fraction(1)]
    for root in roots:
        value=Fraction(float(root))
        b=[Fraction(0)]*(len(a)+1)
        for i,c in enumerate(a):
            b[i]+=c
            b[i+1]-=c*value
        a=b
    return np.array([float(value) for value in a])


def matched_error(actual, expected):
    cost=abs(np.asarray(actual)[:,None]-np.asarray(expected)[None,:])
    columns=minimum_cost_assignment(cost)
    return float(max(cost[np.arange(len(cost)),columns]))


def timed(function,repetitions=7):
    start=perf_counter_ns()
    function()
    warm=max((perf_counter_ns()-start)*1e-9,1e-6)
    batch=max(1,min(2000,math.ceil(0.04/warm)))
    samples=[]
    for i in range(repetitions):
        wall,cpu=perf_counter_ns(),process_time_ns()
        for _ in range(batch):
            function()
        samples.append({'repetition':i+1,'batch':batch,
                        'cpu_ms':(process_time_ns()-cpu)*1e-6/batch,
                        'wall_ms':(perf_counter_ns()-wall)*1e-6/batch})
    return samples


def run_benchmark(folder='resultados/benchmark'):
    folder=Path(folder)
    folder.mkdir(parents=True,exist_ok=True)
    raw,summary,accuracy=[],[],[]
    rng=np.random.default_rng(20261123)
    for family in ('distribuidos','agrupados'):
        for n in (5,10,20):
            roots=-np.linspace(0.5,2,n) if family=='distribuidos' else -1-np.linspace(-0.001,0.001,n)
            coefficients=generated_polynomial(roots)
            model=TransferFunction([1],coefficients)
            gain=0.5*coefficients[-1]
            w=np.geomspace(1e-4,100,2000)
            gains=np.linspace(0,gain,40)
            jobs={'Routh':lambda:routh(model.characteristic(gain)),
                  'Nyquist':lambda:nyquist(model,gain,points=1000),
                  'Lugar das raízes':lambda:root_locus(model,gains),
                  'Bode e margens':lambda:margins(model,gain,w)}
            for method,function in jobs.items():
                records=timed(function)
                for row in records:
                    raw.append({'family':family,'order':n,'method':method,**row})
                summary.append({'family':family,'order':n,'method':method,
                                'cpu_median_ms':float(np.median([r['cpu_ms'] for r in records])),
                                'wall_median_ms':float(np.median([r['wall_ms'] for r in records])),
                                'wall_min_ms':min(r['wall_ms'] for r in records),
                                'wall_max_ms':max(r['wall_ms'] for r in records),
                                'repetitions':len(records),'batch':records[0]['batch']})
            closed_coefficients=model.characteristic(gain)
            exact=exact_routh_count(closed_coefficients)
            root_values=np.roots(coefficients)
            rounded=coefficients.astype(np.float32).astype(float)
            perturbed=coefficients*(1+1e-12*rng.uniform(-1,1,len(coefficients)))
            residual=abs(np.polyval(coefficients,root_values))/np.polyval(abs(coefficients),abs(root_values))
            own_r=routh(closed_coefficients)
            own_n=nyquist(model,gain,points=1000)
            accuracy.append({'family':family,'order':n,'gain':float(gain),
                             'root_error_to_generators_float64':matched_error(root_values,roots),
                             'root_error_to_generators_float32_coefficients':matched_error(np.roots(rounded),roots),
                             'root_movement_under_1e_minus12_relative_perturbation':matched_error(np.roots(perturbed),root_values),
                             'max_scaled_polynomial_residual':float(max(residual)),
                             'exact_rational_routh_rhp':exact,'float_routh_rhp':own_r.right_half_plane_poles,
                             'nyquist_rhp':own_n.closed_loop_unstable,'nyquist_status':own_n.status,
                             'classifications_match':bool(exact==own_r.right_half_plane_poles==own_n.closed_loop_unstable)})
            print(f'{family} n={n}: concluído',flush=True)
    report={'python':platform.python_version(),'numpy':np.__version__,'platform':platform.platform(),
            'processor':platform.processor(),'logical_cpu_count':os.cpu_count(),
            'protocol':{'orders':[5,10,20],'repetitions':7,'warmups':1,'target_batch_wall_s':0.04,
                        'nyquist_initial_points':1000,'bode_points':2000,'root_locus_gains':40,
                        'cpu_clock':'process_time_ns','wall_clock':'perf_counter_ns','plotting_included':False,
                        'note':'Custos de tarefas diferentes, com resolução declarada; não são uma prova de complexidade assintótica.'},
            'summary':summary,'accuracy':accuracy,
            'all_classifications_match':all(row['classifications_match'] for row in accuracy),
            'error_scope':'Erro de raízes inclui arredondamento dos coeficientes e condicionamento do solucionador; resíduo pequeno não garante erro direto pequeno.'}
    with (folder/'tempos_brutos.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=raw[0].keys());writer.writeheader();writer.writerows(raw)
    (folder/'benchmark.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
    for ax,family in zip(axes,('distribuidos','agrupados')):
        for method in jobs:
            rows=[r for r in summary if r['family']==family and r['method']==method]
            ax.plot([r['order'] for r in rows],[r['cpu_median_ms'] for r in rows],'-o',label=method)
        ax.set(xlabel='Ordem do sistema',ylabel='Tempo de CPU mediano (ms)',title=f'Polos {family}',yscale='log',xticks=[5,10,20])
        ax.grid(True,alpha=.3);ax.legend(fontsize=8)
    fig.savefig(folder/'escalabilidade.png',dpi=160);plt.close(fig)
    return report


if __name__=='__main__':
    run_benchmark()
