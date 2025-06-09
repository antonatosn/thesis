"""Flask application entry point."""
import os

from app import create_app  # pylint: disable=import-self

app = create_app()
host = os.environ.get('FLASK_HOST', '0.0.0.0')
port = int(os.environ.get('FLASK_PORT', 5000))
debug = os.environ.get('FLASK_DEBUG', '1').lower() in ('true', '1', 'yes')


if __name__ == '__main__':
    app.run(host=host, port=port, debug=debug)
    print(f"Running on http://{host}:{port} with debug={debug}")
