"""gherkins — lightweight Python deployment pipeline library.

Provides a decorator-based stage pipeline (StageManager) and utilities for
running shell commands locally and on remote servers via SSH (Serloc).

Example::

    from gherkins import StageManager, local_exec, ServerConnection

    sm = StageManager()

    @sm.stage("Deploy")
    def deploy():
        local_exec("docker build -t myapp .")

    sm.run()
"""

from gherkins.StageManager import StageManager
from gherkins.Serloc import local_exec, ServerConnection

__version__ = "0.1.0"
__author__ = "Sravan Gogulapati"

__all__ = ["StageManager", "local_exec", "ServerConnection"]
