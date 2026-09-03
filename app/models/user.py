from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, id, name, email, role):
        self.id = id
        self.name = name
        self.email = email
        self.role = role

    def is_admin(self):
        return self.role == "admin"

    def is_customer(self):
        return self.role == "customer"