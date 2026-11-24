# Evidências reais do simulador PID

Capturas da janela do programa em execução no Windows, sem montagem ou
alteração do conteúdo. São arquivos JPEG produzidos pela ferramenta de
captura de janela; os gráficos exportados pelo programa ficam separadamente
em resultados/simulador/.

Configuração comum: Kp=2; Ki=1; Kd=0,2; Tf=0,05 s; Ts=0,01 s;
duração solicitada de 100 s; planta D e referência de degrau unitário.

| Captura | Conteúdo | Atraso solicitado | Atraso efetivo | Dados da interface |
|---|---|---:|---:|---|
| 01_pid_estavel.jpg | Saída converge e comando se acomoda | 0,59476 s | 0,59 s | resultados/simulador/20261123_230003/ |
| 02_pid_instavel.jpg | Oscilações crescentes; eixos em escala symlog | 1,48690 s | 1,49 s | resultados/simulador/20261123_230028/ |
| 03_nyquist_bode_instavel.jpg | Nyquist com P=0, N=2, Z=2 e Bode | 1,48690 s | 1,49 s | resultados/simulador/20261123_230028/ |

O atraso crítico digital previsto é aproximadamente 0,99127 s e o
contínuo, 0,99735 s. O atraso efetivo é arredondado para amostras inteiras.
No cenário instável, a escala symlog permite enxergar amplitudes positivas
e negativas crescentes sem ocultar o trecho inicial.

Cada pasta exportada pela interface contém simulacao.csv,
configuracao_e_metricas.json, resposta.png e frequencia.png. As configurações
dos prints correspondem a essas execuções. Os experimentos em lote usam
mais casas decimais no atraso solicitado, mas os mesmos atrasos efetivos.

Essas capturas comprovam uma simulação em software. Não comprovam placa
ESP32/Arduino, emulação de microcontrolador ou Hardware-in-the-Loop físico.
