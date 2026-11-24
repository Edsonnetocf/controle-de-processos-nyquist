# Controle de Processos — critérios de estabilidade

Projeto individual de Engenharia da Computação, em Python. Núcleo próprio de
Nyquist, Routh-Hurwitz, Lugar das Raízes e Bode, com margens de estabilidade.

## Estado da entrega

Primeira etapa: modelos, algoritmos e testes matemáticos. O simulador PID,
a validação com bibliotecas externas, os benchmarks nas ordens 5/10/20,
os prints da aplicação e o artigo ainda serão desenvolvidos após aprovação.
Os quatro PNGs atuais são gráficos gerados pelo programa, não capturas de tela
de uma aplicação interativa ou de hardware.

O professor autorizou a substituição da prática física por simulador com
prints e dispensou seminário/demonstração, conforme informação do aluno.

## Executar no Windows

Requer Python 3.11 ou superior. Em um terminal aberto nesta pasta:

Se o ambiente já estiver preparado, basta dar duplo clique em
`EXECUTAR_NUCLEO.bat`: ele executa os testes, gera os gráficos e abre a pasta
dos resultados. Isso ainda não inicia o simulador PID, que está pendente.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe verificar.py
.\.venv\Scripts\python.exe executar.py
```

Não é necessário ativar o ambiente. Para executar só o núcleo com NumPy:

```powershell
.\.venv\Scripts\python.exe executar.py --sem-graficos
```

`executar.py` salva PNG, CSV e JSON em `resultados/nucleo`. `verificar.py`
salva o log real da suíte e um resumo JSON, retornando código diferente de zero
se houver falhas. Para uma execução sem salvar o log:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Organização

```text
src/
  models.py       modelos, resposta complexa e Padé próprio
  nyquist.py      contorno, refinamento, número de envolvimentos e classificação
  routh.py        tabela, casos especiais e contagem de polos instáveis
  root_locus.py   raízes e associação dos ramos pelo algoritmo húngaro
  frequency.py    Bode, cruzamentos e margens
tests/
  test_core.py    referências analíticas e situações adversas
docs/
  MODELOS_E_HIPOTESES.md
  ALGORITMOS_E_LIMITACOES.md
  FONTES.md
resultados/nucleo/  arquivos obtidos em execuções reais
executar.py        demonstração dos quatro sistemas
verificar.py       suíte com evidências de execução
```

## Bibliotecas e implementação própria

NumPy: aritmética, avaliação polinomial, vetores e `numpy.roots` (solucionador
geral de raízes). Matplotlib: apresentação gráfica. Esses recursos não
substituem os algoritmos de controle implementados neste repositório.

`requirements-validacao.txt` lista SciPy e python-control exclusivamente
para a próxima fase de validação. O núcleo atual não importa essas bibliotecas.
`requirements-execucao.txt` registra as versões efetivamente usadas nesta etapa.
O registro de versões corresponde ao Python 3.14.3 usado na execução;
`requirements.txt` permite resolução compatível em outras versões suportadas.

## Como interpretar os resultados

Realimentação negativa unitária: L(s)=K G(s), equação 1+L(s)=0.
Em Nyquist, N conta envolvimentos horários positivos e Z=N+P.
N pode ser negativo: no sistema B estabilizado, P=1 e N=-1, logo Z=0.

`stable` indica ausência de polos instáveis nas condições numéricas verificadas;
`unstable`, presença de polos no semiplano direito; `boundary` e `inconclusive`
nunca devem ser apresentados como estabilidade confirmada. Uma linha nula
de Routh não implica, por si só, estabilidade marginal.

Ausência de cruzamento de margem é registrada como `null`, e não convertida
automaticamente em margem infinita. Margens isoladas não certificam estabilidade.
Para D, Nyquist e Bode usam atraso exponencial; Routh e Lugar das Raízes estão
explicitamente identificados como aproximações de Padé [3/3].

## Reprodutibilidade e GitHub

Repositório público do projeto:
https://github.com/Edsonnetocf/controle-de-processos-nyquist

A primeira etapa está versionada localmente e preparada para publicação.
O desenvolvimento das próximas etapas será registrado no mesmo histórico.
Não há resultados de hardware, benchmarking completo ou validação cruzada
apresentados como realizados.
