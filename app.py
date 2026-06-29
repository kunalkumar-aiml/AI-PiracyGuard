"""Compatibility entrypoint redirecting to the piracyguard package app factory."""

import os
from piracyguard.app import app

if __name__ == "__main__":
    # Start the Flask app using configuration settings
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    port = int(os.environ.get("FLASK_PORT", "5000"))
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug_mode
    )
