import logging

from synckeys.ansible_utils import run_plays
from synckeys.delete_keys.delete_keys_result_callback import DeleteKeysResultCallback


def delete_keys_from_server(dl, acl, private_key, server_name, user, keys, dry_run):
    logging.info(
        "For each key, type Y or n to remove the key from server"
        + server_name
        + "'s authorized keys or not"
    )
    keys_to_remove = []
    for key in keys:
        wish_to_delete_key = input(" - " + key["name"] + " ? (Y/n) ")
        if wish_to_delete_key == "Y":
            keys_to_remove.append(key)
        else:
            continue

    if len(keys_to_remove) > 0:
        play = dict(
            name="Remove keys " + ", ".join([key["name"] for key in keys_to_remove]) + " on server " + server_name,
            hosts=server_name,
            gather_facts='no',
            tasks=[],
            remote_user=user,
            become=True
        )
        key_strings_to_remove = [key["key_string"] for key in keys_to_remove]
        key_names = [key["name"] for key in keys_to_remove]
        if dry_run:
            play['tasks'].append(
                dict(
                    action=dict(
                        module='command',
                        args="echo 'Running authorized_key with args user " + user + "," +
                             " keys " + ", ".join(key_names) + "," +
                             " and state absent'",
                    ),
                    register='shell_out'
                )
            )
            play['tasks'].append(
                dict(action=dict(module='debug', args=dict(msg='{{shell_out.stdout}}'))))
        else:
            play['tasks'].append(
                dict(
                    action=dict(
                        module='authorized_key',
                        args=dict(
                            user=user,
                            key="\n".join(key_strings_to_remove),
                            state="absent"
                        )
                    )
                )
            )
        logging.info("Removing keys " + ", ".join(key_names) + " for user " + user + " from server" + server_name)
        run_plays(dl, acl, private_key, [play], DeleteKeysResultCallback(user, key_names))
    else:
        logging.info("Not removing any keys from " + server_name + " for user " + user)
