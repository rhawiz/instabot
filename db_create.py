#!flask/bin/python

from app import db, app

print("CREATING DB")
print(app.config.get("SQLALCHEMY_DATABASE_URI"))
db.create_all()
