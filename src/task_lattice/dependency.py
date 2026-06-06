from contextlib import AsyncExitStack
import inspect
from typing import Callable


class Depends:
    """Dependency to inject at runtime.

    To use initialise with a function/context manager. E.g.

    def get_context():
        return Context()

    @app.task
    def task_fn(context = Depends(get_context)):
        ...
    """

    def __init__(self, dependency: Callable):
        self.dependency = dependency


async def resolve_dependencies(function, kwargs) -> tuple[dict, AsyncExitStack]:
    """Method to resolve the kwargs passed into a function.

    This will resolve any dependencies using "Depends" class.
    The return value is a stack of context managers and a dict of kwargs.
    """
    signature = inspect.signature(function)

    stack = AsyncExitStack()
    resolved_kwargs = {}

    for name, param in signature.parameters.items():
        if isinstance(param.default, Depends):
            if inspect.iscoroutinefunction(param.default.dependency):
                dep = await param.default.dependency()
            else:
                dep = param.default.dependency()

            if hasattr(dep, "__aenter__"):
                dep = await stack.enter_async_context(dep)
            if hasattr(dep, "__enter__"):
                dep = stack.enter_context(dep)

            resolved_kwargs[name] = dep

        elif name in kwargs:
            resolved_kwargs[name] = kwargs[name]

    return resolved_kwargs, stack
