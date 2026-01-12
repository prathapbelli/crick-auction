import db

db.init_db()
if db.create_user("admin", "admin123"):
    print("User 'admin' created.")
else:
    print("User 'admin' already exists.")
