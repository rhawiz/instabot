#!flask/bin/python

from app import db, app

print("CREATING DB")
print(app.config.get("SQLALCHEMY_DATABASE_URI"))
r = db.create_all()
print(r)