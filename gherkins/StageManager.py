from __future__ import annotations

from typing import Callable
from rich.console import Console


class StageManager:
    """Decorator-based pipeline manager for sequential deployment stages.

    Register stages with the ``@sm.stage()`` decorator and execute them in
    registration order by calling ``sm.run()``.  A subset of stages can be
    selected by name at run time.

    Example::

        sm = StageManager()

        @sm.stage("Build image")
        def build():
            local_exec("docker build -t myapp .")

        @sm.stage("Deploy")
        def deploy():
            server.exec("systemctl restart myapp")

        sm.run()
    """

    def __init__(self) -> None:
        """Initialise an empty stage registry."""
        self.stages: list[tuple[Callable, str]] = []

    def stage(self, stage_name: str) -> Callable:
        """Register a function as a named deployment stage.

        Args:
            stage_name: Human-readable name for the stage.  Used both as the
                display label when the stage runs and as the selector key for
                ``sm.run(stages=[...])``.

        Returns:
            A decorator that registers the wrapped function and returns it
            unchanged, so the function can still be called directly if needed.

        Example::

            @sm.stage("Copy files")
            def copy_files():
                server.scp("./dist", "/opt/app")
        """
        def stage_decorator(func: Callable) -> Callable:
            self.stages.append((func, stage_name))
            return func
        return stage_decorator

    def run(self, stages: list[str] | None = None) -> None:
        """Execute registered stages in order.

        Args:
            stages: Optional list of stage names to run.  When ``None`` (the
                default) every registered stage is executed in registration
                order.  When provided, only the named stages are run, in the
                order they appear in this list.

        Raises:
            ValueError: If any name in *stages* does not match a registered
                stage.

        Example::

            sm.run()                           # run all stages
            sm.run(["Build image", "Deploy"])  # run two specific stages
        """
        console = Console()
        if stages is None:
            stage_list = self.stages
        else:
            stage_map = {name: func for func, name in self.stages}
            unknown = [name for name in stages if name not in stage_map]
            if unknown:
                raise ValueError(
                    f"Unknown stage(s): {unknown}\n"
                    f"Available stages: {list(stage_map.keys())}"
                )
            stage_list = [(stage_map[name], name) for name in stages]
        for func, stage_name in stage_list:
            console.rule(f"[bold green]{stage_name}")
            func()
