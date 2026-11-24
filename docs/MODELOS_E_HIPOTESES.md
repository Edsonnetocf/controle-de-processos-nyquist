# Modelos e hipóteses — primeira etapa

Modelos didáticos aprovados pelo aluno. Não são parâmetros identificados de
equipamentos reais. Todos são contínuos, SISO, com coeficientes reais,
realimentação negativa unitária e ganho K positivo. O atraso é constante em
cada análise de frequência. As unidades de tempo são segundos e as frequências,
rad/s; os modelos adotam normalização didática das demais grandezas.

## Sistema A — estável em malha aberta, terceira ordem

G(s)=1/[(s+1)(s+2)(s+3)].
Polos abertos: -1, -2 e -3. Equação característica:
s³+6s²+11s+(6+K)=0.

Routh exige 6(11)>6+K e 6+K>0. Para K positivo, o intervalo
assintoticamente estável é 0<K<60. Em K=60:
(s+6)(s²+11)=0, com par imaginário ±j√11.
O exemplo dos gráficos usa K=10.

## Sistema B — instável em malha aberta

G(s)=1/[(s-1)(s+2)(s+3)].
Polos abertos: +1, -2 e -3. Equação característica:
s³+4s²+s+(K-6)=0.

Routh exige K-6>0 e 4>K-6, portanto 6<K<10.
Em K=6 há um polo na origem. Em K=10:
(s+4)(s²+1)=0. O exemplo usa K=8: Nyquist deve obter P=1,
N=-1 e Z=0. Estabilidade da planta aberta e da malha fechada são distintas.

## Sistema C — zero no semiplano direito

G(s)=(1-s)/[(s+1)(s+2)(s+3)]. Zero em +1.
Equação característica: s³+6s²+(11-K)s+(6+K)=0.

Para K positivo, a condição limitante é 6(11-K)>6+K,
isto é, 0<K<60/7. No limite, o par imaginário tem frequência √(17/7).
O exemplo usa K=4. Nesse ganho não há cruzamento de magnitude unitária
na faixa analisada; a margem de fase é reportada como ausente, sem inventar valor.

## Sistema D — atraso de transporte

G(s)=exp(-τs)/[(s+1)(0,5s+1)]. Polos da parte racional: -1 e -2.
Exemplo do núcleo: K=2 e τ=0,5 s. A característica exata é
0,5s²+1,5s+1+K exp(-τs)=0: não é um polinômio.

Nyquist e Bode avaliam o exponencial diretamente. A tabela de Routh e
o Lugar das Raízes usam, no exemplo, Padé [3/3], sem confundir esse resultado
aproximado com a análise exata. A aplicação PID digital está descrita em
`SIMULACAO_PID.md`.

## Referência independente para testar atraso

Usa-se também L(s)=2 exp(-τs)/(s+1), exclusivamente como caso de teste.
A condição de magnitude unitária fornece ωc=√3. A primeira perda de
estabilidade ocorre em τcrit=[π-arctan(√3)]/√3 ≈ 1,2092 s.
Os testes verificam estabilidade abaixo e instabilidade acima desse valor,
além de não certificar estabilidade exatamente na fronteira.

## Documentação da etapa prática

As decisões de discretização, sintonia e protocolo experimental foram
documentadas em `SIMULACAO_PID.md` e `REVISAO_ETAPA_2.md`. A simulação
autorizada não é HIL físico nem execução em uma placa real.
