"""
Main Flask application entry point
Initializes the Flask app and registers all API blueprints
"""
from flask import Flask
from auth.auth_controller import auth_bp
from units.unit_controller import unit_bp
from shifts.shift_controller import shift_bp

# Create Flask application instance
app = Flask(__name__)

# Register API blueprints (route modules)
app.register_blueprint(auth_bp)      # Authentication routes: /login
app.register_blueprint(unit_bp)       # Unit management routes: /unit/*
app.register_blueprint(shift_bp)      # Shift management routes: /shift/*

# Run the application in debug mode when executed directly
if __name__ == "__main__":
    app.run(debug=True)
