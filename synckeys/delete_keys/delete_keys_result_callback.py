import logging

from ansible.plugins.callback import CallbackBase


class DeleteKeysResultCallback(CallbackBase):

    def __init__(self, user, keys):
        super().__init__()
        self.user = user
        self.keys = keys

    def v2_runner_on_ok(self, result, **kwargs):
        logging.info(
            "Successfully removed keys "
            + ", ".join(self.keys)
            + " on host "
            + result._host.get_name()
            + " for user "
            + self.user
        )

    def v2_runner_on_failed(self, result, ignore_errors=False):
        logging.error(
            "Couldn't remove keys "
            + ", ".join(self.keys)
            + " on host "
            + result._host.get_name()
            + " for user "
            + self.user
            + " : "
            + self._dump_results(result._result, indent=2)
        )

    def v2_runner_on_unreachable(self, result):
        logging.error(
            "Couldn't remove keys "
            + ", ".join(self.keys)
            + " on host "
            + result._host.get_name()
            + " for user "
            + self.user
            + " : host is unreachable"
        )
