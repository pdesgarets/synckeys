import logging
import jinja2
import os

from tempfile import NamedTemporaryFile
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from collections import namedtuple


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

    Options = namedtuple('Options', ['connection', 'module_path', 'forks', 'become', 'become_method', 'become_user',
                                     'check', 'diff'])
    options = Options(forks=100, connection="ssh", module_path="", become=None, become_method="sudo",
                      become_user="root", check=False, diff=False)

    tqm = None
    try:
        tqm = TaskQueueManager(
            inventory=inventory,
            variable_manager=variable_manager,
            loader=dl,
            options=options,
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
            if results_callback.failures > 0:
                exit(1)
