#!flask/bin/python
from migrate.versioning import api
from config import Config as cfg
from app import db
import os.path
db.create_all()
if not os.path.exists(cfg.SQLALCHEMY_MIGRATE_REPO):
    api.create(cfg.SQLALCHEMY_MIGRATE_REPO, 'database repository')
    api.version_control(cfg.SQLALCHEMY_DATABASE_URI, cfg.SQLALCHEMY_MIGRATE_REPO)
else:
    api.version_control(cfg.SQLALCHEMY_DATABASE_URI, cfg.SQLALCHEMY_MIGRATE_REPO, api.version(cfg.SQLALCHEMY_MIGRATE_REPO))