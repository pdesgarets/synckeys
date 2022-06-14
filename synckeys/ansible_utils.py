import logging
import jinja2
import os

from tempfile import NamedTemporaryFile
from ansible.vars.manager import VariableManager
from ansible.module_utils.common.collections import ImmutableDict
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible import context


def run_plays(dl, acl, private_key, ansible_plays, results_callback):
    logging.debug('Collected ' + str(len(ansible_plays)) + ' Ansible plays. Now running...')

    # Second, configure everything for Ansible
    # We must use a file for the inventory. It will be deleted at the end.

    inventory_template = """
    {% for project in projects %}
    [{{project.name}}]
    {% for server in project.servers %}{{ server }} {% if private_key %} ansible_ssh_private_key_file={{ private_key }} {% endif %}
    {% endfor %}
    {% endfor %}
        """
    inventory_file = NamedTemporaryFile(delete=False, mode="w")
    inventory_file.write(jinja2.Template(inventory_template).render({
        'projects': acl,
        'private_key': private_key
    })
    )
    inventory_file.close()
    inventory = InventoryManager(loader=dl, sources=[inventory_file.name])

    variable_manager = VariableManager(loader=dl, inventory=inventory)

    context.CLIARGS = ImmutableDict(forks=100, connection="ssh", module_path="", become=None, become_method="sudo",
                      become_user="root", check=False, diff=False, verbosity=0)

    tqm = None
    try:
        tqm = TaskQueueManager(
            inventory=inventory,
            variable_manager=variable_manager,
            loader=dl,
            passwords=None,
            stdout_callback=results_callback,  # Use our custom callback
            # instead of the ``default`` callback plugin
        )
        for play in ansible_plays:
            tqm.run(Play().load(
                play, variable_manager=variable_manager, loader=dl))
    finally:
        if tqm is not None:
            os.unlink(inventory_file.name)
            tqm.cleanup()
