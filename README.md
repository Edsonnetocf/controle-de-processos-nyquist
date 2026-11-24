# Controle de Processos — critérios de estabilidade

Projeto individual de Engenharia da Computação, em Python. Núcleo próprio de
Nyquist, Routh-Hurwitz, Lugar das Raízes e Bode, com margens de estabilidade.

## Estado da entrega

Núcleo, validação cruzada, benchmarks nas ordens 5/10/20 e simulador PID
digital implementados. Resultados medidos estão em `resultados/`; capturas
reais da aplicação ficam em `evidencias/`. O artigo de 12 páginas foi preparado
para envio separado pelo Teams. A pasta local `artigo/` é ignorada pelo Git
e não acompanha o clone deste repositório.
Os gráficos exportados não devem ser confundidos com capturas de tela ou
evidências de execução em hardware físico.

O professor autorizou a substituição da prática física por simulador com
prints e dispensou seminário/demonstração, conforme informação do aluno.

## Executar no Windows

Requer Python 3.11 ou superior. Em um terminal aberto nesta pasta:

Se o ambiente já estiver preparado, basta dar duplo clique em
`EXECUTAR_NUCLEO.bat`: ele executa os testes, gera os gráficos e abre a pasta
dos resultados. Para a aplicação interativa, abra `ABRIR_SIMULADOR.bat`.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe verificar.py
.\.venv\Scripts\python.exe executar.py
```

Para repetir a validação externa, o benchmarking e os experimentos de PID:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-validacao.txt
.\.venv\Scripts\python.exe executar_etapa2.py
```

O benchmarking é executado sequencialmente, depois da validação. Evite outras
tarefas pesadas durante essa medição. O tempo de CPU e o tempo decorrido são
registrados separadamente, sem incluir a geração dos gráficos.

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
  pid.py          PID digital, planta ZOH e previsão de atraso crítico
tests/
  test_core.py    referências analíticas e situações adversas
  test_pid.py     buffer de atraso, amostragem e comportamento do PID
docs/
  MODELOS_E_HIPOTESES.md
  ALGORITMOS_E_LIMITACOES.md
  FONTES.md
resultados/nucleo/  arquivos obtidos em execuções reais
executar.py        demonstração dos quatro sistemas
verificar.py       suíte com evidências de execução
validacao_cruzada.py comparação com SciPy e python-control
benchmark.py       CPU e erros nas ordens 5, 10 e 20
experimentos.py    atraso, Padé e PID
simulador_gui.py   interface desktop do experimento
executar_etapa2.py execução sequencial da segunda etapa
```

## Bibliotecas e implementação própria

NumPy: aritmética, avaliação polinomial, vetores e `numpy.roots` (solucionador
geral de raízes). Matplotlib: apresentação gráfica. Esses recursos não
substituem os algoritmos de controle implementados neste repositório.

`requirements-validacao.txt` lista SciPy e python-control exclusivamente
para validação externa. O núcleo em `src/` não importa essas bibliotecas.
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
O limite estático em frequência zero é incluído quando a resposta DC é finita;
isso é importante para a planta B, que pode perder estabilidade ao reduzir K.
Para D, Nyquist e Bode usam atraso exponencial; Routh e Lugar das Raízes estão
explicitamente identificados como aproximações de Padé [3/3].

## Reprodutibilidade e GitHub

Repositório público do projeto:
https://github.com/Edsonnetocf/controle-de-processos-nyquist

A primeira etapa está publicada; as alterações posteriores são registradas
em commits locais e enviadas ao GitHub quando a publicação é autorizada.
O desenvolvimento das próximas etapas será registrado no mesmo histórico.
Não há execução em placa física. A aplicação prática é uma simulação integral
em software, conforme autorização do professor relatada pelo aluno.

## Artigo e organização da entrega

O artigo usa o modelo oficial da SBC. O PDF, a identificação acadêmica e os
fontes editáveis estão apenas na pasta local `artigo/`, para envio separado
ao professor. As tabelas e figuras foram geradas dos JSONs e CSVs medidos,
sem inventar resultados.

`docs/GUIA_DE_ENTREGA.md` organiza os arquivos e registra a licença ainda
pendente. `docs/GUIA_DE_ESTUDO.md` explica os principais resultados e limites.
Os arquivos do artigo estão separados dos scripts necessários para executar
o simulador e os experimentos.
