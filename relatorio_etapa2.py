"""Consolida resultados medidos em um resumo legível, sem inventar números."""
import json
from pathlib import Path


def load(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def generate():
    tests=load('resultados/nucleo/validacao_nucleo.json')
    validation=load('resultados/validacao/validacao_cruzada.json')
    benchmark=load('resultados/benchmark/benchmark.json')
    experiments=load('resultados/experimentos/experimentos.json')
    limits=experiments['pid_limits']
    lines=['# Revisão da segunda etapa','',
           '## Testes e validação cruzada','',
           f'- Suíte: {tests["test_methods"]} testes; {tests["failures"]} falhas; {tests["errors"]} erros.',
           f'- Comparações racionais: {len(validation["cases"])} configurações; mais {len(validation["exact_delay_cases"])} casos de atraso exato com referência analítica.',
           f'- Todas as verificações externas passaram: {"sim" if validation["all_passed"] else "não"}.',
           f'- Erro máximo da planta ZOH versus SciPy: {validation["plant_zoh_max_error"]:.4g}.',
           f'- Erro máximo da resposta PID versus filtro digital externo: {validation["pid_time_series_max_error"]:.4g}.',
           '', 'A comparação externa identificou e motivou a correção do cruzamento estático',
           'de fase da planta B em frequência zero. Os testes incluem regressão desse caso.',
           'SciPy e python-control compartilham algumas operações NumPy com o núcleo;',
           'as referências analíticas e a aritmética racional complementam a validação.',
           '', '## Desempenho medido','',
           'Tempo de CPU mediano por execução, em ms. Sete repetições em lotes após',
           'aquecimento; custo de gráficos excluído. Dados brutos incluem tempo decorrido.',
           'Bode inclui a extração de margens; Lugar das Raízes usa 40 ganhos.','',
           '| Família | Ordem | Routh | Nyquist | Lugar das Raízes | Bode e margens |',
           '|---|---:|---:|---:|---:|---:|']
    for family in ('distribuidos','agrupados'):
        for n in (5,10,20):
            values={r['method']:r['cpu_median_ms'] for r in benchmark['summary'] if r['family']==family and r['order']==n}
            lines.append(f'| {family} | {n} | '+ ' | '.join(f'{values[m]:.4f}' for m in ['Routh','Nyquist','Lugar das raízes','Bode e margens'])+' |')
    lines+=['','As resoluções e tarefas são diferentes; os tempos não provam uma hierarquia',
            'universal de complexidade. A máquina e as versões estão no JSON.','',
            '## Condicionamento numérico','',
            '| Família | Ordem | Erro de raízes float64 | Coeficientes float32 | Resíduo escalado máximo |',
            '|---|---:|---:|---:|---:|']
    for row in benchmark['accuracy']:
        lines.append(f'| {row["family"]} | {row["order"]} | {row["root_error_to_generators_float64"]:.4g} | {row["root_error_to_generators_float32_coefficients"]:.4g} | {row["max_scaled_polynomial_residual"]:.4g} |')
    lines+=['','O erro de raízes é medido em relação às raízes geradoras, incluindo o efeito',
            'do arredondamento dos coeficientes. Resíduo pequeno não garante erro direto',
            'pequeno. Uma perturbação relativa de até 1e-12 também foi testada.',
            f'Contagens de Routh, Nyquist e referência racional exata concordantes: {"sim" if benchmark["all_classifications_match"] else "não"}.',
            'A referência racional analisa exatamente os coeficientes float64 recebidos,',
            'não recupera o polinômio ideal anterior ao arredondamento.','',
            '## Aplicação PID e atraso','',
            f'- Atraso crítico contínuo previsto: {limits["continuous_s"]:.8f} s.',
            f'- Atraso crítico digital previsto: {limits["digital_s"]:.8f} s para Ts={limits["sample_time_s"]} s.',
            '- São modelos diferentes: retenção da planta e discretização do PID alteram a fronteira.',
            '', '| Cenário | Atraso efetivo (s) | Máximo de abs(y) | Máximo erro no trecho final |',
            '|---|---:|---:|---:|']
    for row in experiments['pid_cases']:
        m=row['metrics']
        lines.append(f'| {row["name"]} | {m["effective_delay_s"]:.4f} | {m["max_abs_output"]:.5g} | {m["tail_max_abs_error"]:.5g} |')
    lines+=['','O trecho final corresponde aos últimos 20% da execução; próximo da fronteira',
            'o amortecimento é lento e 100 s podem não ser suficientes para acomodação.',
            'O cenário instável é interrompido se atingir o limite numérico declarado.',
            'Não se afirma execução em ESP32, Arduino ou HIL físico.','',
            '## Comparação de Padé','']
    mismatches=[row for row in experiments['pade_comparison'] if not row['classification_matches']]
    for row in mismatches:
        lines.append(f'- τ={row["tau_s"]} s, Padé ordem {row["order"]}: Z aproximado={row["approximate_rhp"]}, Z exato={row["exact_rhp"]}.')
    if not mismatches:lines.append('Não houve divergência de classificação nos casos executados.')
    article_status=('Artigo de 12 páginas preparado para envio separado pelo Teams. '
                    'A pasta artigo/ é local, ignorada pelo Git e não acompanha o repositório público.')
    lines+=['','Foram medidos erros complexos RMS e máximos em 0,01 a 30 rad/s para ordens',
            '1, 3, 5 e 7. Concordância de classificação não significa aproximação exata.','',
            '## Evidências da interface','',
            'Três capturas reais da janela estão em evidencias/: cenário estável,',
            'cenário instável e Nyquist/Bode do caso instável. O arquivo LEIA-ME.md',
            'relaciona os prints às configurações e aos dados exportados pela interface.','',
            '## Estado da entrega','',
            article_status,
            'Repositório público mantido sem licença adicional, conforme decisão do autor. Não há pendência de licenciamento para esta entrega.',
            'A publicação de novos commits é tratada separadamente da validação local.']
    Path('docs/REVISAO_ETAPA_2.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__=='__main__':generate()
