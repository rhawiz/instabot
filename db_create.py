#!flask/bin/python

from app import db, logger

print("CREATING DB")
db.create_all()
