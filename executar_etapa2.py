"""Executa sequencialmente validação, benchmarks e experimentos reais."""
import subprocess
import sys
from validacao_cruzada import run_validation
from benchmark import run_benchmark
from experimentos import run_experiments
from relatorio_etapa2 import generate


if __name__=='__main__':
    subprocess.run([sys.executable,'verificar.py'],check=True)
    if not run_validation()['all_passed']:
        raise SystemExit('Validação cruzada falhou; consulte os resultados antes de prosseguir.')
    run_benchmark()
    run_experiments()
    generate()
    print('Etapa experimental concluída. Consulte resultados/ e docs/.')
