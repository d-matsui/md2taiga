from flask import (
    Blueprint, flash, render_template, request
)
from . import md2taiga_cli
import taiga.exceptions

bp = Blueprint('index', __name__)


@bp.route('/', methods=('GET', 'POST'))
def index():
    text = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hostname = request.form['hostname']
        project_name = request.form['project_name']
        text = request.form['text']

        error = None
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif not hostname:
            error = 'Hostname is required.'
        elif not project_name:
            error = 'Project name is required.'
        elif not text:
            error = 'Markdown text is required.'
        try:
            api = md2taiga_cli.init_taiga_api(hostname, username, password)
            api.projects.get_by_slug(project_name)
        except taiga.exceptions.TaigaRestException as e:
            if str(e) == 'NETWORK ERROR':
                error = 'Network Error. Check your hostname is correct.'
            else:
                error = str(e)

        if error is None:
            # TODO: Should use md2taiga_cli module
            api = md2taiga_cli.init_taiga_api(hostname, username, password)
            project = api.projects.get_by_slug(project_name)
            lines = text.splitlines()
            level = md2taiga_cli.calc_min_level(lines)
            userstories = md2taiga_cli.create_us_list(lines, level, project)
            text_converted = ''
            for us in userstories:
                line = f'- {us["title"]}\n'
                text_converted += line
                for task in us['task_list']:
                    line = f'\t- {task["title"]}\n'
                    text_converted += line
            if 'create' in request.form:
                md2taiga_cli.add_us_to_project(userstories, project)
                return render_template('index.html')
            return render_template('index.html', username=username, password=password, hostname=hostname, project_name=project_name, text=text, text_converted=text_converted, userstories=userstories)

        flash(error)
    if text != '':
        return render_template('index.html', text=text)
    return render_template('index.html')
