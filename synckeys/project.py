from synckeys.user import User


class Project:
    def __init__(self, project_yaml):
        self.name = project_yaml['name']
        self.servers = project_yaml['servers']
        self.users = []
        for username, useracl in project_yaml['users'].items():
            self.users.append(User(username, useracl))

    def get_sudoer_account(self, keyname):
        for user in self.users:
            if user.is_sudoer() and user.is_authorized(keyname):
                return user
        return None
