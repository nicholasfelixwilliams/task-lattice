import asyncio
from contextlib import asynccontextmanager, contextmanager

from task_lattice.dependency import Depends, resolve_dependencies


def sync_dep():
    return 42


async def async_dep():
    return 42


@contextmanager
def sync_ctx_dep():
    yield "sync_ctx"


@asynccontextmanager
async def async_ctx_dep():
    yield "async_ctx"


class TestResolveDependencies:
    def test_sync_dependency_injected(self):
        def fn(value=Depends(sync_dep)): ...

        result, _ = asyncio.run(resolve_dependencies(fn, {}))
        assert result["value"] == 42

    def test_async_dependency_injected(self):
        def fn(value=Depends(async_dep)): ...

        result, _ = asyncio.run(resolve_dependencies(fn, {}))
        assert result["value"] == 42

    def test_sync_context_manager_injected(self):
        def fn(value=Depends(sync_ctx_dep)): ...

        async def run():
            result, stack = await resolve_dependencies(fn, {})
            async with stack:
                return result

        result = asyncio.run(run())
        assert result["value"] == "sync_ctx"

    def test_async_context_manager_injected(self):
        def fn(value=Depends(async_ctx_dep)): ...

        async def run():
            result, stack = await resolve_dependencies(fn, {})
            async with stack:
                return result

        result = asyncio.run(run())
        assert result["value"] == "async_ctx"

    def test_plain_kwargs_passed_through(self):
        def fn(x, y): ...

        result, _ = asyncio.run(resolve_dependencies(fn, {"x": 1, "y": 2}))
        assert result == {"x": 1, "y": 2}

    def test_mixed_deps_and_kwargs(self):
        def fn(x, dep=Depends(sync_dep)): ...

        result, _ = asyncio.run(resolve_dependencies(fn, {"x": 99}))
        assert result["x"] == 99
        assert result["dep"] == 42
