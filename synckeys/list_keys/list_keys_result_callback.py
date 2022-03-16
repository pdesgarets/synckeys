import logging
import json

from ansible.parsing.ajson import AnsibleJSONDecoder
from ansible.plugins.callback import CallbackBase

from synckeys.delete_keys.delete_keys import delete_keys_from_server


class ListKeysResultCallback(CallbackBase):

    def __init__(self, dl, acl, private_key, dry_run):
        super().__init__()
        self.dl = dl
        self.acl = acl
        self.private_key = private_key
        self.dry_run = dry_run

    def get_user(self, result):
        result_dict = json.loads(
            self._dump_results(result._result, indent=2, keep_invocation=True), cls=AnsibleJSONDecoder
        )
        return result_dict["invocation"]["module_args"]["chdir"].split("/")[-1]

    def v2_runner_on_ok(self, result, **kwargs):
        result_dict = json.loads(
            self._dump_results(result._result, indent=2, keep_invocation=True), cls=AnsibleJSONDecoder
        )
        key_strings = result_dict["stdout_lines"]
        user = self.get_user(result)
        key_names = [key.split(" ")[-1] for key in key_strings]
        keys = [{"key_string": key_strings[i], "name": key_names[i]} for i in range(len(key_strings))]
        logging.info(
            "\n"
            + "#################################################################################################\n\n"
            + "Server " + result._host.get_name() + ", User " + user + "\n\n"
            + "\n".join(key_names)
        )
        logging.info(
            "\n"
            + "------------------------------"
            + "\n"
        )
        wish_to_delete_some_keys = input(
            "Do you wish to remove at least one key from this server's authorized keys for user " + user + " ? (Y/n) "
        )
        if wish_to_delete_some_keys == "Y":
            delete_keys_from_server(
                self.dl,
                self.acl,
                self.private_key,
                result._host.get_name(),
                user,
                keys,
                self.dry_run
            )
        else:
            logging.info("Not removing any keys from " + result._host.get_name() + " for user " + user)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        logging.error(
            "Couldn't list keys on host "
            + result._host.get_name()
            + " for user "
            + self.get_user(result)
            + " : "
            + self._dump_results(result._result, indent=2)
        )

    def v2_runner_on_unreachable(self, result):
        logging.error(
            "Couldn't list keys on host "
            + result._host.get_name()
            + " for user "
            + self.get_user(result)
            + " : host is unreachable"
        )
