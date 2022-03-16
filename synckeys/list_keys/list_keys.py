import logging

from synckeys.list_keys.list_keys_result_callback import ListKeysResultCallback
from synckeys.ansible_utils import run_plays
from synckeys.project import Project


def list_keys(dl, acl, keyname, project_name, private_key, dry_run):
    ansible_plays = []
    # First, collect all tasks to perform
    for project_yaml in acl:
        project = Project(project_yaml)
        if project_name and project.name != project_name:
            continue
        ansible_plays.extend(get_project_list_keys_play(project, keyname))
    run_plays(dl, acl, private_key, ansible_plays, ListKeysResultCallback(dl, acl, private_key, dry_run))


def get_project_list_keys_play(project, keyname):
    sudoer_account = project.get_sudoer_account(keyname)

    logging.info('Listing authorized keys in project "' + project.name + '" using key "' + keyname + '"')
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

        play = dict(
            name="List authorized keys for " + user.name + " on " + project.name,
            hosts=project.name,
            gather_facts='no',
            tasks=[
                dict(
                    action=dict(
                        module='command',
                        args=dict(
                            chdir="/home/" + user.name,
                            cmd="cat .ssh/authorized_keys"
                        )
                    )
                )
            ],
            remote_user=remote_user,
            become=use_sudo
        )
        plays.append(play)
    return plays
