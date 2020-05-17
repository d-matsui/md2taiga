from flask import Flask
import os


def create_app():
    # create and configure the app
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.urandom(24)
    )

    from . import index
    app.register_blueprint(index.bp)
    app.add_url_rule('/', endpoint='index')

    return app
