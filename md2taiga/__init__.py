from flask import Flask
import os


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.urandom(24)
    )

    if test_config is not None:
        app.config.from_mapping(test_config)

    from . import index
    app.register_blueprint(index.bp)
    app.add_url_rule('/', endpoint='index')

    return app
