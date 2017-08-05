#!flask/bin/python

from app import db, app

print("CREATING DB")
print(app.config.get("DATABASE_URL"))
db.create_all()
