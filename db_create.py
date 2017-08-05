#!flask/bin/python

from app import db, logger

logger.info("CREATING DATABASE")
db.create_all()
