# Revisão da segunda etapa

## Testes e validação cruzada

- Suíte: 48 testes; 0 falhas; 0 erros.
- Comparações racionais: 10 configurações; mais 2 casos de atraso exato com referência analítica.
- Todas as verificações externas passaram: sim.
- Erro máximo da planta ZOH versus SciPy: 1.966e-12.
- Erro máximo da resposta PID versus filtro digital externo: 1.24e-09.

A comparação externa identificou e motivou a correção do cruzamento estático
de fase da planta B em frequência zero. Os testes incluem regressão desse caso.
SciPy e python-control compartilham algumas operações NumPy com o núcleo;
as referências analíticas e a aritmética racional complementam a validação.

## Desempenho medido

Tempo de CPU mediano por execução, em ms. Sete repetições em lotes após
aquecimento; custo de gráficos excluído. Dados brutos incluem tempo decorrido.
Bode inclui a extração de margens; Lugar das Raízes usa 40 ganhos.

| Família | Ordem | Routh | Nyquist | Lugar das Raízes | Bode e margens |
|---|---:|---:|---:|---:|---:|
| distribuidos | 5 | 0.0651 | 1.9531 | 5.2083 | 4.2614 |
| distribuidos | 10 | 0.1365 | 2.4038 | 11.7188 | 5.2083 |
| distribuidos | 20 | 0.3524 | 3.9062 | 23.4375 | 11.7188 |
| agrupados | 5 | 0.0585 | 1.9531 | 5.2083 | 4.2614 |
| agrupados | 10 | 0.1313 | 1.9531 | 7.8125 | 5.8594 |
| agrupados | 20 | 0.2367 | 3.3482 | 23.4375 | 11.7188 |

As resoluções e tarefas são diferentes; os tempos não provam uma hierarquia
universal de complexidade. A máquina e as versões estão no JSON.

## Condicionamento numérico

| Família | Ordem | Erro de raízes float64 | Coeficientes float32 | Resíduo escalado máximo |
|---|---:|---:|---:|---:|
| distribuidos | 5 | 1.505e-13 | 1.505e-13 | 1.377e-16 |
| distribuidos | 10 | 5.118e-10 | 0.1685 | 1.109e-16 |
| distribuidos | 20 | 0.1701 | 1.12 | 2.237e-16 |
| agrupados | 5 | 0.000481 | 0.05042 | 2.083e-17 |
| agrupados | 10 | 0.04965 | 0.3891 | 8.788e-17 |
| agrupados | 20 | 0.3829 | 1.173 | 2.158e-16 |

O erro de raízes é medido em relação às raízes geradoras, incluindo o efeito
do arredondamento dos coeficientes. Resíduo pequeno não garante erro direto
pequeno. Uma perturbação relativa de até 1e-12 também foi testada.
Contagens de Routh, Nyquist e referência racional exata concordantes: sim.
A referência racional analisa exatamente os coeficientes float64 recebidos,
não recupera o polinômio ideal anterior ao arredondamento.

## Aplicação PID e atraso

- Atraso crítico contínuo previsto: 0.99734556 s.
- Atraso crítico digital previsto: 0.99126689 s para Ts=0.01 s.
- São modelos diferentes: retenção da planta e discretização do PID alteram a fronteira.

| Cenário | Atraso efetivo (s) | Máximo de abs(y) | Máximo erro no trecho final |
|---|---:|---:|---:|
| sem_atraso | 0.0000 | 1 | 2.7756e-15 |
| estavel | 0.5900 | 1.4561 | 1.1594e-11 |
| proximo_limite | 0.9400 | 1.8802 | 0.13686 |
| instavel | 1.4900 | 3.8518e+05 | 3.8518e+05 |

O trecho final corresponde aos últimos 20% da execução; próximo da fronteira
o amortecimento é lento e 100 s podem não ser suficientes para acomodação.
O cenário instável é interrompido se atingir o limite numérico declarado.
Não se afirma execução em ESP32, Arduino ou HIL físico.

## Comparação de Padé

- τ=1.3 s, Padé ordem 1: Z aproximado=0, Z exato=2.

Foram medidos erros complexos RMS e máximos em 0,01 a 30 rad/s para ordens
1, 3, 5 e 7. Concordância de classificação não significa aproximação exata.

## Evidências da interface

Três capturas reais da janela estão em evidencias/: cenário estável,
cenário instável e Nyquist/Bode do caso instável. O arquivo LEIA-ME.md
relaciona os prints às configurações e aos dados exportados pela interface.

## Estado da entrega

Artigo de 12 páginas preparado para envio separado pelo Teams. A pasta artigo/ é local, ignorada pelo Git e não acompanha o repositório público.
Licença de código aberto ainda depende da escolha do autor.
A publicação de novos commits é tratada separadamente da validação local.
