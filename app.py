from flask import Flask
from flask_login import LoginManager
from database import db
from models.models import User
from routes.auth import auth_bp
from routes.clients import clients_bp
from routes.admin import admin_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', name='ADMIN', role='ADMIN')
        admin.set_password('123')
        db.session.add(admin)
        db.session.commit()

app.register_blueprint(auth_bp)
app.register_blueprint(clients_bp)
app.register_blueprint(admin_bp)

if __name__ == '__main__':
    app.run(debug=True)
