"""Interface desktop do experimento PID. Execução: python simulador_gui.py."""
import json
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import datetime
from dataclasses import asdict
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from src.pid import PIDConfig, delay_limits, continuous_loop, simulate_pid
from src.frequency import bode
from src.nyquist import nyquist


class Simulator:
    def __init__(self,root):
        self.root=root
        root.title('Controle de Processos | Laboratório PID')
        root.geometry('1320x850')
        root.minsize(1120,760)
        root.configure(bg='#edf2f5')
        style=ttk.Style(root)
        style.theme_use('clam')
        style.configure('.',font=('Segoe UI',10))
        style.configure('TFrame',background='#edf2f5')
        style.configure('TLabel',background='#edf2f5',foreground='#203547')
        style.configure('TLabelframe',background='#edf2f5')
        style.configure('TLabelframe.Label',background='#edf2f5',foreground='#203547',font=('Segoe UI',10,'bold'))
        style.configure('TButton',padding=(10,8))
        style.configure('Accent.TButton',background='#087f8c',foreground='white',font=('Segoe UI',10,'bold'))
        style.configure('TNotebook.Tab',padding=(16,9))
        header=tk.Frame(root,bg='#172e46',height=83)
        header.pack(fill='x')
        tk.Label(header,text='LABORATÓRIO DE ESTABILIDADE',font=('Segoe UI',19,'bold'),bg='#172e46',fg='white').pack(anchor='w',padx=22,pady=(13,0))
        tk.Label(header,text='PID digital • planta de segunda ordem • atraso de comunicação',font=('Segoe UI',11),bg='#172e46',fg='#b9d8e6').pack(anchor='w',padx=23,pady=(3,13))
        body=ttk.Frame(root,padding=16)
        body.pack(fill='both',expand=True)
        left=ttk.Frame(body,width=260)
        left.pack(side='left',fill='y',padx=(0,15))
        left.pack_propagate(False)
        controls=ttk.LabelFrame(left,text=' Configuração do experimento ',padding=12)
        controls.pack(fill='x')
        self.values={}
        fields=[('kp','Ganho proporcional Kp','2'),('ki','Ganho integral Ki','1'),('kd','Ganho derivativo Kd','0.2'),
                ('tf','Filtro da derivada Tf (s)','0.05'),('ts','Amostragem Ts (s)','0.01'),
                ('delay','Atraso solicitado τ (s)','0.4'),('duration','Duração (s)','100')]
        for row,(key,label,value) in enumerate(fields):
            ttk.Label(controls,text=label).grid(row=row*2,column=0,sticky='w',pady=(5,2))
            variable=tk.StringVar(value=value)
            ttk.Entry(controls,textvariable=variable,width=25).grid(row=row*2+1,column=0,sticky='ew',pady=(0,3))
            self.values[key]=variable
        controls.columnconfigure(0,weight=1)
        ttk.Button(left,text='Simular configuração',style='Accent.TButton',command=self.run).pack(fill='x',pady=(12,7))
        presets=ttk.Frame(left)
        presets.pack(fill='x')
        ttk.Button(presets,text='Caso estável',command=lambda:self.preset(.6)).pack(side='left',expand=True,fill='x',padx=(0,4))
        ttk.Button(presets,text='Caso instável',command=lambda:self.preset(1.5)).pack(side='left',expand=True,fill='x')
        ttk.Button(left,text='Exportar dados e gráfico',command=self.export).pack(fill='x',pady=(8,10))
        ttk.Label(left,text='Modelo didático em software.\nSem placa física ou HIL.\nSem saturação do atuador.\nAtraso arredondado para amostras.',wraplength=250,font=('Segoe UI',9)).pack(anchor='w',pady=5)
        right=ttk.Frame(body)
        right.pack(side='left',fill='both',expand=True)
        self.summary=tk.StringVar()
        ttk.Label(right,textvariable=self.summary,font=('Segoe UI',11,'bold'),wraplength=1000).pack(anchor='w',pady=(0,9))
        self.notebook=ttk.Notebook(right)
        self.notebook.pack(fill='both',expand=True)
        response_tab,frequency_tab,details_tab=[ttk.Frame(self.notebook) for _ in range(3)]
        self.notebook.add(response_tab,text='Resposta e controle')
        self.notebook.add(frequency_tab,text='Nyquist e Bode')
        self.notebook.add(details_tab,text='Dados e hipóteses')
        self.time_figure=Figure(figsize=(9,6),dpi=100,layout='constrained',facecolor='white')
        self.time_axes=self.time_figure.subplots(2,1,sharex=True)
        self.time_canvas=FigureCanvasTkAgg(self.time_figure,master=response_tab)
        self.time_canvas.get_tk_widget().pack(fill='both',expand=True)
        self.frequency_figure=Figure(figsize=(9,6),dpi=100,layout='constrained',facecolor='white')
        self.frequency_axes=self.frequency_figure.subplots(2,2)
        self.frequency_canvas=FigureCanvasTkAgg(self.frequency_figure,master=frequency_tab)
        self.frequency_canvas.get_tk_widget().pack(fill='both',expand=True)
        self.details=tk.Text(details_tab,font=('Consolas',11),wrap='word',bg='white',fg='#203547',padx=16,pady=14,borderwidth=0)
        self.details.pack(fill='both',expand=True)
        self.footer=tk.StringVar(value='Pronto')
        ttk.Label(root,textvariable=self.footer,anchor='w',padding=(18,7)).pack(fill='x')
        self.result=None
        self.root.after(100,self.run)

    def config(self):
        value={key:float(v.get().replace(',','.')) for key,v in self.values.items()}
        return PIDConfig(value['kp'],value['ki'],value['kd'],value['tf'],value['ts']),value

    def preset(self,factor):
        try:
            cfg,_=self.config()
            limit=delay_limits(cfg)['digital_s']
            self.values['delay'].set(f'{factor*limit:.5f}')
            self.run()
            self.notebook.select(0)
        except ValueError as error:messagebox.showerror('Configuração inválida',str(error))

    def run(self):
        try:
            cfg,values=self.config()
            self.limits=delay_limits(cfg)
            result=simulate_pid(cfg,values['delay'],values['duration'])
            self.prediction=nyquist(continuous_loop(cfg,result.effective_delay))
            self.result=result
            metrics=result.metrics()
            state={'stable':'ESTÁVEL','unstable':'INSTÁVEL','boundary':'FRONTEIRA','inconclusive':'INCONCLUSIVO'}[self.prediction.status]
            self.summary.set(f'Nyquist contínuo: {state}   |   atraso aplicado: {result.effective_delay:.3f} s   |   limite digital previsto: {self.limits["digital_s"]:.3f} s')
            for ax in self.time_axes:ax.clear()
            self.time_axes[0].plot(result.time,result.output,color='#087f8c',lw=1.5,label='Saída da planta')
            self.time_axes[0].axhline(1,color='#d47b31',ls='--',label='Referência = 1')
            self.time_axes[0].set(ylabel='Saída y(t)',title=f'Resposta ao degrau — atraso de {result.effective_delay:.3f} s')
            self.time_axes[1].plot(result.time,result.command,color='#375b92',lw=1,label='Comando PID')
            self.time_axes[1].plot(result.time,result.delayed_command,color='#d47b31',lw=.8,alpha=.8,label='Comando recebido pela planta')
            self.time_axes[1].set(xlabel='Tempo (s)',ylabel='Comando u(t)')
            for ax,series in zip(self.time_axes,[result.output,result.command]):
                if max(abs(series))>10:
                    ax.set_yscale('symlog',linthresh=2)
                    ax.set_ylabel(ax.get_ylabel()+' (escala symlog)')
                ax.grid(True,alpha=.25);ax.legend(fontsize=9,loc='upper right')
            self.time_canvas.draw()
            model=continuous_loop(cfg,result.effective_delay)
            w=np.geomspace(.01,100,3500)
            response=model.frequency_response(w)
            b=bode(model,w)
            for ax in self.frequency_axes.flat:ax.clear()
            ax=self.frequency_axes[0,0]
            ax.plot(response.real,response.imag,color='#087f8c',label='ω > 0')
            ax.plot(response.real,-response.imag,'--',color='#7abbbd',label='ω < 0')
            ax.plot(-1,0,'rx',ms=8,mew=2)
            ax.set(xlim=(-3,2),ylim=(-3,3),xlabel='Parte real',ylabel='Parte imaginária',title='Nyquist contínuo — detalhe do ponto -1')
            ax.legend(fontsize=8)
            ax=self.frequency_axes[0,1]
            ax.semilogx(w,b.magnitude_db,color='#087f8c');ax.axhline(0,color='gray',ls='--')
            ax.set(xlabel='ω (rad/s)',ylabel='Magnitude (dB)',title='Bode — magnitude')
            ax=self.frequency_axes[1,0]
            ax.semilogx(w,b.phase_deg,color='#087f8c');ax.axhline(-180,color='gray',ls='--')
            ax.set(xlabel='ω (rad/s)',ylabel='Fase (graus)',title='Bode — fase com atraso',ylim=(-540,0))
            ax=self.frequency_axes[1,1]
            ax.axis('off')
            ax.text(.02,.9,f'P = {self.prediction.open_loop_unstable}\nN horário = {self.prediction.clockwise_encirclements}\nZ = {self.prediction.closed_loop_unstable}\n\nLimite contínuo: {self.limits["continuous_s"]:.4f} s\nLimite digital: {self.limits["digital_s"]:.4f} s\n\nA previsão contínua não inclui\no efeito da amostragem digital.',va='top',fontsize=11,transform=ax.transAxes)
            for ax in self.frequency_axes.flat:
                if ax.axison:ax.grid(True,alpha=.25)
            self.frequency_canvas.draw()
            lines=['EXPERIMENTO EM SOFTWARE — ENGENHARIA DA COMPUTAÇÃO','',
                   'Planta: G(s) = 1 / [(s+1)(0,5s+1)]',
                   'PID: integral trapezoidal; derivada filtrada na medição.',
                   'Planta atualizada exatamente com entrada constante por amostra.',
                   'Atraso constante em cada execução, arredondado para amostras.',
                   'Sem saturação; resultados de estabilidade para modelo linear.',
                   '','PREVISÕES',json.dumps(self.limits,ensure_ascii=False,indent=2),
                   '','RESULTADOS OBSERVADOS',json.dumps(metrics,ensure_ascii=False,indent=2),
                   '','Uma execução finita não prova estabilidade assintótica.',
                   'Os gráficos de frequência usam o modelo contínuo com atraso exato.',
                   'O limite digital considera o controlador discreto e retenção da planta.']
            self.details.configure(state='normal');self.details.delete('1.0','end');self.details.insert('1.0','\n'.join(lines));self.details.configure(state='disabled')
            self.footer.set(f'Ts = {cfg.sample_time:g} s • {result.delay_samples} amostras de atraso • erro final = {1-result.output[-1]:.5g}'+(' • Interrompido por limite numérico' if result.stopped_early else ' • Execução concluída'))
        except (ValueError,ArithmeticError) as error:messagebox.showerror('Não foi possível simular',str(error))

    def export(self):
        if self.result is None:return
        folder=Path('resultados/simulador')/datetime.now().strftime('%Y%m%d_%H%M%S')
        folder.mkdir(parents=True,exist_ok=True)
        result=self.result
        np.savetxt(folder/'simulacao.csv',np.c_[result.time,result.output,result.command,result.delayed_command],delimiter=',',header='time_s,output,command,delayed_command')
        (folder/'configuracao_e_metricas.json').write_text(json.dumps({'metrics':result.metrics(),'limits':self.limits,'continuous_nyquist_status':self.prediction.status},ensure_ascii=False,indent=2),encoding='utf-8')
        self.time_figure.savefig(folder/'resposta.png',dpi=160)
        self.frequency_figure.savefig(folder/'frequencia.png',dpi=160)
        self.footer.set(f'Dados e gráficos exportados em {folder}. Capturas da janela devem ser feitas separadamente.')


if __name__=='__main__':
    root=tk.Tk()
    app=Simulator(root)
    root.mainloop()
