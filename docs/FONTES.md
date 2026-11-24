# Fontes e situação de consulta

## Enunciado efetivamente lido

AED- Projeto_Pesquisa_Criterio_Nyquist_CC_EC.pdf, três páginas, fornecido pelo
aluno. Objetivos, sistemas de teste, metodologia e entregáveis foram extraídos
desse documento. Alterações de escopo: relato do aluno sobre dispensa do
seminário e autorização para simulador com prints.

## Documentação técnica consultada em 23/11/2026

- NumPy, `numpy.roots`: https://numpy.org/doc/stable/reference/generated/numpy.roots.html
  Confirma o solucionador de raízes polinomiais, com coeficientes decrescentes.
- Python Control Systems Library, `nyquist_response`:
  https://python-control.readthedocs.io/en/latest/generated/control.nyquist_response.html
  Referência de comportamento para contornos e desvios de polos; não usada
  como implementação do núcleo.
- Python Control Systems Library, `margin`:
  https://python-control.readthedocs.io/en/latest/generated/control.margin.html
  Referência para escolha de margem quando existem múltiplos cruzamentos.

## Documentação adicional consultada para a segunda etapa

- SciPy, `cont2discrete`: https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.cont2discrete.html
  Referência de discretização ZOH, usada exclusivamente para validar a planta.
- Python Control Systems Library, `root_locus_map`:
  https://python-control.readthedocs.io/en/latest/generated/control.root_locus_map.html
- Python Control Systems Library, `stability_margins`:
  https://python-control.readthedocs.io/en/latest/generated/control.stability_margins.html

## Livros recomendados no enunciado, ainda não consultados integralmente

- OGATA, Katsuhiko. Engenharia de Controle Moderno. 5ª ed. Pearson, 2010.
- NISE, Norman S. Engenharia de Sistemas de Controle. 7ª ed. LTC, 2017.
- ÅSTRÖM, Karl J.; MURRAY, Richard M. Feedback Systems: An Introduction for
  Scientists and Engineers. Princeton University Press, 2008.

As informações acima reproduzem a indicação do enunciado; não representam
verificação independente dessas edições ou citação de trechos dos livros.
