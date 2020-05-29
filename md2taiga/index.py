from flask import (
    Blueprint, flash, render_template, request
)
from . import md2taiga_cli
import taiga.exceptions

bp = Blueprint('index', __name__)


@bp.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'GET':
        return render_template('index.html')

    username = request.form['username']
    password = request.form['password']
    hostname = request.form['hostname']
    project_name = request.form['project_name']
    milestone_name = ''.join(request.form['milestone_name'].split())
    text = request.form['text']
    text_converted = request.form['text_converted']

    error = validate_inputs(username, password, hostname, project_name, text, text_converted)

    try:
        api = md2taiga_cli.init_taiga_api(hostname, username, password)
        project = api.projects.get_by_slug(project_name)
    except taiga.exceptions.TaigaRestException as e:
        if str(e) == 'NETWORK ERROR':
            error = 'Network Error. Check your hostname is correct.'
        else:
            error = str(e)

    if error is None:
        # TODO: Should be able to specify status and tag by GUI
        status_name = 'New'
        tag_name = 'team: dev'
        # TODO: Should handle error
        status = project.us_statuses.get(name=status_name).id
        tags = {tag_name: project.list_tags()[tag_name]}
        userstories = md2taiga_cli.create_us_list(text, project, status, tags, milestone_name)

        if 'convert' in request.form:
            text_converted = md2taiga_cli.convert_text(userstories)
            return render_template('index.html', text=text, text_converted=text_converted)

        md2taiga_cli.add_us_to_project(userstories, project)
        return render_template('index.html')

    flash(error)
    return render_template('index.html', text=text)


def validate_inputs(username, password, hostname, project_name, text, text_converted):
    error = None
    if not username:
        error = 'Username is required.'
    elif not password:
        error = 'Password is required.'
    elif not hostname:
        error = 'Hostname is required.'
    elif not project_name:
        error = 'Project name is required.'
    elif not text and 'convert' in request.form:
        error = 'Markdown text is required.'
    elif not text_converted and 'create' in request.form:
        error = 'You need to convert markdown text before creating user stories.'

    return error
