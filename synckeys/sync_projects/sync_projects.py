import logging
import datetime

from synckeys.ansible_utils import run_plays
from synckeys.project import Project
from synckeys.sync_projects.sync_projects_result_callback import SyncProjectsResultCallback

def _convert_to_date(date_str):
    if isinstance(date_str, datetime.date):
        return date_str
    if isinstance(date_str, datetime.datetime):
        return date_str.date()
    return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()

def get_project_play(project, keys, keyname, dry_run):

    logging.info('Syncing "' + project.name + '" using key "' + keyname + '"')
    plays = []

    for user in project.users:
        if user.is_authorized(keyname):
            # we have direct access to this user, no need to use sudo
            remote_user = user.name
            use_sudo = False
        elif sudoer_account:
            logging.info('sudoer "' + sudoer_account.name + '"')
            # we are allowed to update this user through the sudo user
            remote_user = sudoer_account.name
            use_sudo = True
        else:
            # we skip since we are not authorized to update this user
            continue

        # if we are authorized, let us update this user's keys
        authorized_key_names = []
        expired_key_names = []
        for key_name in user.acl['authorized_keys']:
            if key_name not in keys:
                logging.error(key_name + ' missing from keys file')
                expired_key_names.append(key_name)
                continue

            if not keys[key_name]['expires'] or _convert_to_date(keys[key_name]['expires']) > datetime.datetime.now().date():
                authorized_key_names.append(key_name)
            else:
                expired_key_names.append(key_name)

        play = dict(
            name="Key setting for " + user.name + " on " + project.name,
            hosts=project.name,
            gather_facts='no',
            tasks=[],
            remote_user=remote_user,
        )
        if use_sudo:
            play["become"] = True
        if len(expired_key_names) > 0:
            expired_keys = [keys[key_name]['key'] + ' ' + key_name for key_name in expired_key_names]
            if dry_run:
                play['tasks'].append(
                    dict(
                        action=dict(
                            module='command',
                            args="echo 'Running authorized_key with args user " + user.name + "," +
                                 " keys " + ",".join(expired_key_names) + "," +
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
                                user=user.name,
                                key="\n".join(expired_keys),
                                state="absent"
                            )
                        )
                    )
                )
            logging.info(' - ' + user.name + ' expired for ' +
                         ", ".join(expired_key_names) + ' synced through ' + remote_user)

        if len(authorized_key_names) > 0:
            authorized_keys = [keys[key_name]['key'] + ' ' + key_name for key_name in authorized_key_names]
            if dry_run:
                play['tasks'].append(
                    dict(
                        action=dict(
                            module='command',
                            args="echo 'Running authorized_key with args user " + user.name + "," +
                                 " keys " + ",".join(authorized_key_names) + "," +
                                 " and state present'",
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
                                user=user.name,
                                key="\n".join(authorized_keys),
                                state="present"
                            )
                        )
                    )
                )
            logging.info(' - ' + user.name + ' authorized for ' +
                         ", ".join(authorized_key_names) + ' synced through ' + remote_user)
        plays.append(play)
    return plays


def sync_acl(dl, acl, keys, keyname, project_name, dry_run, private_key):
    ansible_plays = []

    # First, collect all tasks to perform
    for project_yaml in acl:
        project = Project(project_yaml)
        if project_name and project.name != project_name:
            continue
        ansible_plays.extend(get_project_play(project, keys, keyname, dry_run))
    run_plays(dl, acl, private_key, ansible_plays, SyncProjectsResultCallback())
