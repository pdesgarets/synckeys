# The unix user (e.g. www-data, operator)
# not the Illuin user !
class User:
    def __init__(self, name, acl):
        self.name = name
        self.acl = acl

    def is_sudoer(self):
        if 'sudoer' in self.acl:
            return self.acl['sudoer']
        else:
            return False

    def is_authorized(self, keyname):
        return keyname in self.acl['authorized_keys']
