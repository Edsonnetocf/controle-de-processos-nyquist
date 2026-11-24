# Algoritmos e limites de interpretação

## Nyquist

O caminho sobe pelo eixo imaginário de -jR a +jR e retorna pelo semicírculo
direito, em sentido horário. Polos sobre o eixo são contornados à direita e
excluídos da região. Avalia-se F(s)=1+K G(s) em todo o caminho. O raio dos
desvios é reduzido até que um limite triangular inferior de |K G(s)| seja
maior que 10 no círculo inteiro, sem zeros abertos em seu interior. Pelo
argumento de Rouché, isso evita ocultar zeros fechados dentro dos desvios.
Se a escala necessária for pequena demais, o resultado é inconclusivo.

O somatório dos incrementos principais do argumento, dividido por -2π,
fornece N horário assinado. P é a contagem de polos abertos estritamente
à direita; Z=N+P. Distância muito pequena do ponto crítico gera `boundary`.

O refinamento insere pontos médios quando há curvatura significativa,
incrementos grandes de fase ou risco de subamostragem do atraso. A contagem
é repetida com dobro do raio e da malha e metade do desvio. Antes disso,
o raio é ampliado até um majorante triangular de |K G(s)| ser menor que 0,1
para todo Re(s)>=0 e |s|>=R. Assim, o trecho descartado não pode conter zeros
de 1+K G(s), dentro das hipóteses do modelo e da aritmética usada.

Limites: a certificação é numérica, não aritmética intervalar. Tolerância de
1e-9 é usada para localizar polos próximos do eixo; parte real pequena mas
não exatamente nula gera resultado inconclusivo, em vez de certificação.
Sistemas mal condicionados exigem análise adicional.
A distância crítica padrão é 1e-7. Há limites de refinamento; falha de
convergência produz resultado inconclusivo. A versão atual exige função
estritamente própria e rejeita cancelamentos polo-zero detectados, pois
eles podem esconder instabilidade interna. Raízes repetidas e ordens altas
serão investigadas separadamente no benchmarking.

## Routh-Hurwitz

Os coeficientes são normalizados e distribuídos nas duas primeiras linhas.
Cada linha seguinte resulta da recorrência de Routh. O escalonamento
positivo por linha preserva os sinais. Um pivô nulo recebe epsilon positivo;
uma linha inteira nula é substituída pelos coeficientes da derivada do
polinômio auxiliar da linha anterior.

Trocas de sinal na primeira coluna contam polos no semiplano direito.
Nos casos de linha nula sem trocas, o resultado é `boundary`, sem afirmar
estabilidade marginal: podem existir raízes imaginárias repetidas.

Limites: epsilon e a tolerância de zero são aproximações numéricas. Os testes
incluem repetição com três epsilons em um caso de pivô nulo. Polinômios perto
da fronteira ou muito mal condicionados exigem variação de tolerâncias e
referências adicionais. Não se aplica diretamente ao atraso exponencial.

## Lugar das Raízes

Para cada ganho K, calculam-se as raízes de D+K N via `numpy.roots`.
Os ramos são associados por minimização global da distância quadrática
entre raízes consecutivas, com implementação própria do algoritmo húngaro.

Limites: o traçado é amostrado em K; detalhes entre amostras não são
garantidos. Em raízes múltiplas a identidade individual dos ramos é ambígua.
A rotina exige função estritamente própria, ganhos não negativos ordenados
e modelo racional. Padé deve ser solicitado explicitamente para atrasos.

## Bode e margens

Magnitude e fase vêm da avaliação complexa. Desembrulha-se a fase racional
antes de subtrair ωτ, evitando aliasing do exponencial em malhas espaçadas.
Os cruzamentos são localizados na malha e refinados por bisseção em log(ω).
Todos os cruzamentos encontrados são registrados; a margem selecionada é
a mais próxima de zero grau ou de ganho unitário em escala logarítmica.
Quando a resposta em zero é finita, o limite estático também é avaliado,
mesmo que a malha positiva de frequências comece acima de zero. Essa
correção foi motivada pela comparação externa da planta B com K=5.

Limites: a busca é finita. Ausência de cruzamento significa `None`/`null`,
nunca prova automática de margem infinita. Contatos tangenciais e cruzamentos
muito próximos podem escapar à busca por mudanças de sinal. A fase racional
também depende de resolução adequada. Margens não substituem o Nyquist
generalizado, especialmente para plantas instáveis em malha aberta.

## O que os testes demonstram nesta etapa

Concordância com referências analíticas nos casos declarados, tratamento
dos casos especiais e consistência das operações. Não demonstram correção
universal, precisão em toda ordem polinomial ou atendimento da etapa final.
A validação cruzada e os ensaios n=5,10,20 estão descritos nos relatórios
da segunda etapa, preservando os limites das conclusões experimentais.
