# Guia para compreender e defender o projeto

## O que foi desenvolvido

Uma ferramenta didática em Python que implementa Nyquist, Routh-Hurwitz,
Lugar das Raízes e Bode, compara os resultados e simula um controlador PID
digital com atraso. Não foi criado um critério matemático novo.

## Perguntas e respostas essenciais

**Por que uma planta estável pode ficar instável quando é realimentada?**
Porque os polos fechados são raízes de D(s)+K N(s), e não apenas de D(s).
Na planta A, o aumento de K até 60 leva um par de polos ao eixo imaginário.

**Como a planta B aberta instável pode ser estabilizada?**
Ela tem P=1 e, para K=8, o Nyquist possui N=-1 na convenção horária positiva.
Assim, Z=N+P=0. O intervalo analítico completo é 6<K<10.

**Por que N pode ser negativo?**
N é uma contagem com sinal. Envolvimento anti-horário tem sinal negativo na
convenção adotada. A orientação do contorno e o sinal da contagem precisam
ser consistentes; contar apenas o número de voltas sem orientação falha.

**O que significa o zero no semiplano direito da planta C?**
É uma característica de fase não mínima. Ele altera a resposta de fase e
limita as possibilidades de controle, mesmo com todos os polos abertos
no semiplano esquerdo. O limite de ganho obtido é 60/7.

**Por que o atraso afeta a estabilidade sem mudar o módulo?**
O módulo do exponencial em s=jω é 1, mas sua fase é -ωτ. Essa fase adicional
pode levar a curva ao ponto crítico -1 e provocar instabilidade.

**Qual foi a evidência concreta da limitação de Padé?**
Na planta D com K=2 e atraso de 1,3 s, Padé de primeira ordem indicou Z=0,
enquanto o atraso exponencial indicou Z=2. Portanto, baixa ordem não garante
preservação da estabilidade. Ordens maiores reduziram o erro nos ensaios.

**Por que os limites de atraso do PID contínuo e digital são diferentes?**
O digital inclui amostragem, retenção da planta e fórmulas discretas do PID.
Para Ts=0,01 s, as previsões foram aproximadamente 0,99735 s e 0,99127 s.
Reduzir Ts aproximou as duas previsões. A diferença não é um erro do critério.

**O programa usa NumPy, então os algoritmos são próprios?**
Sim, no sentido declarado: Nyquist, Routh, busca de margens, associação de
ramos e simulação foram implementados no projeto. O solucionador geral
numpy.roots e a aritmética NumPy foram utilizados explicitamente. SciPy e
python-control aparecem apenas na validação externa.

**Um resíduo pequeno garante uma raiz precisa?**
Não. Em ordem 20, o erro de localização chegou a cerca de 0,17 na família
distribuída mesmo com resíduo de ordem 1e-16. O polinômio pode ser muito
sensível ao arredondamento dos coeficientes.

**Routh sempre resolve tudo mais rápido?**
Ele foi o mais rápido no protocolo medido, mas fornece informação diferente
de uma varredura de raízes ou de margens. Os resultados não estabelecem uma
hierarquia universal de custo. A resolução e a quantidade de ganhos importam.

**Uma linha nula em Routh significa estabilidade?**
Não. É necessário tratar o polinômio auxiliar e examinar as raízes de
fronteira. Raízes imaginárias repetidas, por exemplo, exigem cautela.

**Os prints são de um microcontrolador?**
Não. São capturas reais do simulador Python em software, alternativa
aprovada para a prática. Não há placa física, emulação de ESP32 ou HIL.

**O atraso varia durante a execução?**
Nesta versão, ele é constante em cada execução e ajustável entre
experimentos. Não foi simulado jitter aleatório dentro da execução.

**Como mostrar que os resultados foram realmente obtidos?**
Relacione artigo, JSONs, CSVs, log dos 48 testes, capturas da interface e
commit 4758fb8. Os scripts permitem repetir os experimentos. Figuras
sozinhas não substituem os dados e as configurações.

**Quais são os limites da prática?**
Modelo linear, planta normalizada, sem saturação ou ruído, atraso quantizado
em amostras e janela finita. A previsão matemática e a simulação devem ser
interpretadas juntas. A aplicação não representa um equipamento real identificado.
