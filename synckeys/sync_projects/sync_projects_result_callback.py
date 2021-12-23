import json
import logging

from ansible.plugins.callback import CallbackBase


class SyncProjectsResultCallback(CallbackBase):
    failures = 0

    def v2_runner_on_ok(self, result, **kwargs):
        logging.debug("SUCCESS for " + result._host.get_name() + " : " + self._dump_results(result._result, indent=2))

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.failures += 1
        logging.error("FAILURE for " + result._host.get_name() + " : " + self._dump_results(result._result, indent=2))
        logging.error("Command was " + json.dumps(result._task._ds["action"], indent=2))

    def v2_runner_on_unreachable(self, result):
        self.failures += 1
        logging.error(
            "UNREACHABLE for " + result._host.get_name() + " : " + self._dump_results(result._result, indent=2))
