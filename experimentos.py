"""Experimentos reproduzíveis de atraso, Padé e PID digital."""
import json
from dataclasses import replace
from pathlib import Path
import numpy as np
from src.models import benchmark_models
from src.nyquist import nyquist
from src.pid import PIDConfig, delay_limits, continuous_loop, simulate_pid


def run_experiments(folder='resultados/experimentos'):
    folder=Path(folder)
    folder.mkdir(parents=True,exist_ok=True)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    cfg=PIDConfig()
    limits=delay_limits(cfg)
    cases=[]
    fig,axes=plt.subplots(2,1,figsize=(11,7),sharex=True,layout='constrained')
    for name,factor in [('sem_atraso',0),('estavel',0.6),('proximo_limite',0.95),('instavel',1.5)]:
        tau=factor*limits['digital_s']
        result=simulate_pid(cfg,tau,100)
        prediction=nyquist(continuous_loop(cfg,result.effective_delay))
        metrics=result.metrics()
        cases.append({'name':name,'factor_of_digital_limit':factor,'metrics':metrics,
                      'continuous_nyquist_status':prediction.status,'continuous_nyquist_rhp':prediction.closed_loop_unstable})
        np.savetxt(folder/f'pid_{name}.csv',np.c_[result.time,result.output,result.command,result.delayed_command],
                   delimiter=',',header='time_s,output,command,delayed_command')
        label=f'{name.replace("_"," ")}: τ={result.effective_delay:.2f} s'
        axes[0].plot(result.time,result.output,label=label,lw=1.1)
        axes[1].plot(result.time,result.command,label=label,lw=1.1)
    axes[0].axhline(1,color='black',ls='--',label='Referência')
    axes[0].set(ylabel='Saída y(t)',title='PID digital — estabilidade depende do atraso')
    axes[1].set(xlabel='Tempo (s)',ylabel='Comando u(t)')
    for ax in axes:ax.set_yscale('symlog',linthresh=2)
    for ax in axes:ax.grid(True,alpha=.3);ax.legend(fontsize=8,loc='upper left')
    fig.savefig(folder/'pid_comparacao.png',dpi=160);plt.close(fig)
    sampling=[]
    for ts in (0.02,0.01,0.005,0.0025):
        config=replace(cfg,sample_time=ts)
        item=delay_limits(config)
        result=simulate_pid(config,0.4,60)
        item['metrics_at_delay_04s']=result.metrics()
        sampling.append(item)
    # Padé: erro em resposta complexa, além da classificação de estabilidade.
    pade=[]
    w=np.geomspace(0.01,30,1500)
    for tau in (0.5,1.0,1.2,1.3,1.6):
        exact=benchmark_models(tau)['D']
        reference=exact.frequency_response(w,2)
        exact_n=nyquist(exact,2)
        for order in (1,3,5,7):
            approximate=exact.pade(order)
            approximate_n=nyquist(approximate,2)
            error=abs(approximate.frequency_response(w,2)-reference)
            pade.append({'tau_s':tau,'order':order,'exact_rhp':exact_n.closed_loop_unstable,
                         'approximate_rhp':approximate_n.closed_loop_unstable,
                         'classification_matches':approximate_n.closed_loop_unstable==exact_n.closed_loop_unstable,
                         'max_abs_frequency_response_error':float(max(error)),
                         'rms_abs_frequency_response_error':float(np.sqrt(np.mean(error**2))),
                         'frequency_range_rad_s':[float(w[0]),float(w[-1])]})
    report={'pid_limits':limits,'pid_cases':cases,'sampling_convergence':sampling,'pade_comparison':pade,
            'scope':'Simulação integral em software, não HIL físico. Planta exata entre amostras; atraso quantizado. Sem saturação.'}
    (folder/'experimentos.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    axes[0].plot([r['sample_time_s'] for r in sampling],[r['digital_s'] for r in sampling],'-o',label='Previsão digital')
    axes[0].axhline(limits['continuous_s'],ls='--',color='black',label='Previsão contínua')
    axes[0].set(xlabel='Período de amostragem (s)',ylabel='Atraso crítico previsto (s)',title='Efeito da amostragem');axes[0].legend(fontsize=8)
    for tau in (0.5,1.3,1.6):
        rows=[r for r in pade if r['tau_s']==tau]
        axes[1].plot([r['order'] for r in rows],[r['rms_abs_frequency_response_error'] for r in rows],'-o',label=f'τ={tau:g} s')
    axes[1].set(xlabel='Ordem de Padé',ylabel='Erro RMS complexo na malha',yscale='log',title='Aproximação do atraso');axes[1].legend(fontsize=8)
    for ax in axes:ax.grid(True,alpha=.3)
    fig.savefig(folder/'atraso_e_pade.png',dpi=160);plt.close(fig)
    print(json.dumps({'pid_limits':limits,'pid_cases':[{ 'name':r['name'],'delay':r['metrics']['effective_delay_s'],
          'max_output':r['metrics']['max_abs_output'],'tail_error':r['metrics']['tail_max_abs_error']} for r in cases],
          'pade_mismatches':[r for r in pade if not r['classification_matches']]},ensure_ascii=False,indent=2))
    return report


if __name__=='__main__':run_experiments()
