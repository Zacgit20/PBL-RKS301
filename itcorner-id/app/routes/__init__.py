from .main import main_bp
from .auth import auth_bp
from .customer import customer_bp
from .admin import admin_bp


def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(admin_bp)