# --------------------------------------------------------------------------
# Change the routing for log database and the main database based on app' name
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - database_router.py
# Created at 2020-8-29,  16:4:57
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

class DatabaseRouter:
    """
    A router to control all database operations on models in the
    CGG applications.
    """
    log_apps = ('api_request',)

    def db_for_read(self, model, **hints):
        """
        Attempts to from database.
        """
        if model._meta.app_label in self.log_apps:
            return 'log'
        return 'default'

    def db_for_write(self, model, **hints):
        """
        Attempts to write auth and contenttypes models go to auth_db.
        """
        if model._meta.app_label in self.log_apps:
            return 'log'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        # Allow any relation if a both models in log app
        if obj1._meta.app_label in self.log_apps and \
                obj2._meta.app_label in self.log_apps:
            return True
        # Allow if neither is log app
        if obj1._meta.app_label not in self.log_apps and \
                obj2._meta.app_label not in self.log_apps:
            return True
        return False

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the auth and contenttypes apps only appear in the
        'auth_db' database.
        """
        if app_label in self.log_apps:
            return db == 'log'

        return db == 'default'
