from flask import Flask


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)

    from . import index
    app.register_blueprint(index.bp)
    app.add_url_rule('/', endpoint='index')

    return app
