import asyncio
from types import SimpleNamespace

from app.tenderproof.solari_adapter import confirm_browser_released


def test_delete_success_without_terminal_get_is_not_confirmation():
    class Sessions:
        async def get(self, _): return {"status": "active"}
    assert not asyncio.run(confirm_browser_released(SimpleNamespace(sessions=Sessions()), "id", timeout=.01))


def test_provider_404_is_unknown_not_closed():
    class Sessions:
        async def get(self, _): raise RuntimeError("404")
    assert not asyncio.run(confirm_browser_released(SimpleNamespace(sessions=Sessions()), "id", timeout=.1))


def test_provider_released_confirms_closure():
    class Sessions:
        async def get(self, _): return {"status": "released"}
    assert asyncio.run(confirm_browser_released(SimpleNamespace(sessions=Sessions()), "id", timeout=.1))


def test_only_official_ibgp_accordion_can_be_expanded():
    from app.tenderproof.solari_adapter import SolariBrowserAdapter
    calls = []
    class Locator:
        @property
        def first(self): return self
        async def count(self): return 1
        async def click(self, **kwargs): calls.append(kwargs)
    class Page:
        def locator(self, selector):
            assert selector == "a[href='#collapseTwo']"
            return Locator()
    adapter = SolariBrowserAdapter()
    asyncio.run(adapter._open_ibgp_edital_section(Page(), "https://portal.imeso.com.br/edital/ver/139"))
    assert not calls
    asyncio.run(adapter._open_ibgp_edital_section(Page(), "https://novo.ibgpconcursos.com.br/concurso.jsp?cod=704"))
    assert calls == [{"timeout": 5000}]
    adapter.close()
