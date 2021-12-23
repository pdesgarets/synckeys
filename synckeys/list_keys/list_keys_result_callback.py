import logging
import json

from ansible.parsing.ajson import AnsibleJSONDecoder

from synckeys.sync_projects.result_callback import ResultCallback


class ListKeysResultCallback(ResultCallback):

    def v2_runner_on_ok(self, result, **kwargs):
        keys_string = json.loads(self._dump_results(result._result, indent=2), cls=AnsibleJSONDecoder)["stdout"]
        key_names = [key.split(" ")[-1] for key in keys_string.split("\n")]
        logging.info(
            "\n"
            + "#################################################################################################\n\n"
            + "Server " + result._host.get_name() + "\n\n"
            + "\n".join(key_names)
        )
