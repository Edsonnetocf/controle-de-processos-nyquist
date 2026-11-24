# Revisão da primeira etapa — 23/11/2026

## Escopo concluído

Quatro plantas didáticas documentadas; Nyquist com contorno e contagem própria;
tabela de Routh com casos especiais; Lugar das Raízes com associação própria
dos ramos; Bode e margens; aproximação de Padé por recorrência; execução
reprodutível e documentação das limitações.

## Verificação executada

38 métodos de teste aprovados, sem falhas, erros ou testes ignorados.
Alguns métodos contêm múltiplos subcasos. O log completo e o horário real
constam em `resultados/nucleo/testes.txt` e `validacao_nucleo.json`.

Cobertura: limites analíticos A/B/C; pivô e linha nula em Routh; variação de
epsilon; polinômios construídos com polos conhecidos; convenção de Nyquist;
planta aberta instável; integrador e desvios; fronteiras críticas; atraso com
limite analítico; grandes ganhos exigindo contorno maior; pequenos ganhos
com polos fechados próximos da origem; Bode e margens analíticas; associação
húngara contra busca exaustiva; resíduos polinomiais do Lugar das Raízes.

## Resultados demonstrativos obtidos

| Sistema | K | Atraso (s) | P | N horário | Z | MG (fator) | MF (graus) |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | 10 | 0 | 0 | 0 | 0 | 6,0000 | 90,0000 |
| B | 8 | 0 | 1 | -1 | 0 | 1,2500 | 2,5379 |
| C | 4 | 0 | 0 | 0 | 0 | 2,1429 | sem cruzamento encontrado |
| D | 2 | 0,5 | 0 | 0 | 0 | 1,8790 | 55,1325 |

Todos os quatro exemplos escolhidos estão estáveis em malha fechada pela
análise numérica de Nyquist. Os testes também abrangem ganhos instáveis,
portanto esses exemplos não afirmam estabilidade para todo ganho.

MG é um multiplicador do ganho atual, não o ganho absoluto. Em B, a condição
analítica completa é 6<K<10; reduzir K também pode desestabilizar. A margem
apresentada no exemplo corresponde ao cruzamento de fase encontrado em
frequência positiva, e não substitui esse intervalo completo.

Em D, Nyquist e Bode mantêm o atraso exponencial. Routh e Lugar das Raízes
usam Padé [3/3] no exemplo. Sua concordância nesta configuração não constitui
validação geral da aproximação.

## Arquivos revisados visualmente

Quatro painéis PNG, um por sistema, com Nyquist, magnitude, fase e Lugar das
Raízes. São exportações gráficas reais do código; não são prints de uma
interface interativa. CSVs e JSON preservam os dados e as configurações.

## Próxima etapa, aguardando aprovação

Validação cruzada com SciPy/python-control, benchmarking n=5/10/20,
comparação de ordens de Padé, simulador PID digital com atraso configurável
e capturas reais da aplicação. Artigo e publicação no GitHub ainda pendentes.
