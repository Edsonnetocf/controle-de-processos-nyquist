# Aplicação de Engenharia da Computação — PID digital em software

## Modelo e sintonia

Planta D: G(s)=1/[(s+1)(0,5s+1)]. Controlador contínuo de referência:
C(s)=Kp+Ki/s+Kd s/(Tf s+1).

Parâmetros didáticos: Kp=2, Ki=1, Kd=0,2, Tf=0,05 s, Ts=0,01 s.
São uma escolha demonstrativa verificada para a planta normalizada; não
representam uma sintonia ótima ou identificação de equipamento real.

O controlador é digital: integral por regra trapezoidal, derivada filtrada
por diferença regressiva. A derivada atua na medição, evitando o impulso
derivativo de uma mudança de referência. Para a equação característica,
a realimentação tem o mesmo controlador completo C(z); o numerador da
resposta à referência usa apenas PI, pois a derivada recebe a saída.

## Planta com atualização exata

Estados: x'=-x+u_d, y'=2(x-y). Para a=exp(-Ts), b=exp(-2Ts):

- x[k+1]=a x[k]+(1-a)u_d[k];
- y[k+1]=b y[k]+2(a-b)x[k]+(1-a)²u_d[k].

Essas expressões são exatas para entrada constante no intervalo, dispensando
integração numérica aproximada da planta. Sua implementação foi comparada
com `scipy.signal.cont2discrete` em espaço de estados, com método ZOH.

## Atraso de comunicação

Uma fila recebe o comando atual e entrega à planta o comando de d amostras
antes. d=floor(τ/Ts+0,5); o atraso efetivo é d Ts, informado no programa.
Não há atraso extra artificial para d=0. O histórico anterior ao início é zero.

Cada execução usa atraso constante. O usuário pode alterá-lo entre execuções;
isso não caracteriza uma simulação de jitter aleatório dentro da execução.
O termo 'variável' é usado no sentido de parâmetro ajustável experimentalmente.

## Previsões e comparação

O Nyquist contínuo avalia C(s)G(s)exp(-τs), incluindo o desvio do integrador.
O primeiro limite de atraso é obtido pela fase disponível nos cruzamentos
de ganho. Separadamente, a resposta digital usa z=exp(jωTs), planta ZOH e
controlador discreto. Verifica-se estabilidade sem atraso antes da previsão.

Para os parâmetros padrão há um cruzamento digital de ganho na faixa
analisada. O limite digital em segundos é contínuo como previsão de fase;
a experiência de tempo usa atrasos inteiros e só resolve a fronteira em Ts.

As previsões contínua e digital diferem pela amostragem e pelas fórmulas do
controlador. A convergência é verificada com Ts de 0,02 a 0,0025 s. Não se
atribui essa diferença a erro de Nyquist.

## Escopo das evidências

Simulação integral em Python/Tkinter, não emulador de ESP32, placa física ou
HIL. Isso corresponde à opção de simulador próprio aprovada pelo aluno.
O atuador não possui saturação: o estudo é linear e demonstra divergência.
Um limite de segurança numérico interrompe amplitudes excessivas e registra
explicitamente a interrupção; não representa um limitador físico do atuador.

Uma janela finita convergindo não prova estabilidade assintótica. As
conclusões combinam previsão em frequência, casos de referência e simulação.
O botão Exportar salva dados e gráficos; os prints em `evidencias/` são
capturas reais da janela, feitas separadamente.
