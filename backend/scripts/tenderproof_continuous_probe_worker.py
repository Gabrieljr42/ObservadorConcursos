"""Synthetic crash fixture for the isolated Celery integration probe only.

The production task is unchanged; this test module supplies an observable
download barrier so its worker can be killed after a durable detail checkpoint.
"""
import os
from pathlib import Path
import time

from app.worker import celery_app
from app.tenderproof.continuous import ContinuousEngine
from app.tenderproof.mock_demo import build_mock_driver
import app.tenderproof.continuous_tasks as tasks


def probe_driver(source,settings,allow_browser=False):
    root=Path(os.environ["TENDERPROOF_PROBE_ROOT"])
    driver=build_mock_driver()
    driver._listing_html=('<a href="/concurso.jsp?cod=42">Concurso Prefeitura Municipal de Exemplo MG cod 42</a>'
                          '<ul class="pagination"><li class="next disabled">Próxima</li></ul>')
    download=driver.download
    def gated(url,*,max_bytes):
        if (root/"crash-gate").exists():
            (root/"download-barrier-reached").write_text(str(os.getpid()),encoding="utf-8")
            while (root/"crash-gate").exists():
                time.sleep(0.1)
        return download(url,max_bytes=max_bytes)
    driver.download=gated
    return driver


tasks.ContinuousEngine=lambda:ContinuousEngine(driver_factory=probe_driver)
celery_app.conf.update(broker_transport_options={"visibility_timeout":5},worker_prefetch_multiplier=1)
