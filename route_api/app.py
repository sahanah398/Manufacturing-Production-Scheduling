"""
Main Flask application entry point
Initializes the Flask app and registers all API blueprints
"""
from flask import Flask
from auth.auth_controller import auth_bp
from units.unit_controller import unit_bp
from shifts.shift_controller import shift_bp
from workstations.workstation_controller import workstation_bp
from processes.process_controller import process_bp
from routes.route_controller import route_bp
from products.product_controller import product_bp

# Create Flask application instance
app = Flask(__name__)

# Register API blueprints (route modules)
app.register_blueprint(auth_bp)      # Authentication routes: /login
app.register_blueprint(unit_bp)       # Unit management routes: /unit/*
app.register_blueprint(shift_bp)      # Shift management routes: /shift/*
app.register_blueprint(workstation_bp) # Workstation routes: /workstation/*
app.register_blueprint(process_bp)    # Process routes: /process/*
app.register_blueprint(route_bp)      # Route routes: /route/*
app.register_blueprint(product_bp)    # Product routes: /product/*

# Run the application in debug mode when executed directly
if __name__ == "__main__":
    app.run(debug=True)
