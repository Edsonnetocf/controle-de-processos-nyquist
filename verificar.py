"""Executa a suíte e salva evidências textuais verificáveis, sem imagens fabricadas."""
import io
import json
import platform
import sys
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np


if __name__ == '__main__':
    folder = Path('resultados/nucleo')
    folder.mkdir(parents=True, exist_ok=True)
    log = io.StringIO()
    suite = unittest.defaultTestLoader.discover('tests')
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    text = log.getvalue()
    (folder/'testes.txt').write_text(text, encoding='utf-8')
    report = {
        'executed_at_sao_paulo': datetime.now(ZoneInfo('America/Sao_Paulo')).isoformat(),
        'python': platform.python_version(), 'numpy': np.__version__,
        'test_methods': result.testsRun, 'failures': len(result.failures),
        'errors': len(result.errors), 'skipped': len(result.skipped),
        'success': result.wasSuccessful(),
        'scope': 'Referências analíticas, consistência matemática e casos especiais. '
                 'Não substitui validação cruzada ou benchmarking da próxima etapa.',
    }
    (folder/'validacao_nucleo.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(text)
    sys.exit(0 if result.wasSuccessful() else 1)
