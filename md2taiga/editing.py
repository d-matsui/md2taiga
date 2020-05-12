from flask import (
    Blueprint, flash, g, render_template, request, session
)
from md2taiga.auth import login_required

# TODO: Should use md2taiga_cli module
import re
from taiga import TaigaAPI
from collections import deque, defaultdict

bp = Blueprint('editing', __name__, url_prefix='/editing')


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        text = request.form['text']
        project_name = request.form['project_name']
        error = None

        if not project_name:
            error = 'Project name is required.'
        elif not text:
            error = 'Markdown text is required.'

        if error is not None:
            flash(error)
        else:
            # TODO: Should use md2taiga_cli module
            # FIXME: Must not hardcode password
            api = init_taiga_api(g.user['hostname'], g.user['username'], '')
            project = api.projects.get_by_slug(project_name)
            lines = text.splitlines()
            level = calc_min_level(lines)
            userstories = create_us_list(lines, level, project)
            # TODO: Need to simplify this
            if 'add_us' in request.form:
                add_us_to_project(userstories, project)
                return render_template('editing/create.html')
            return render_template('editing/create.html', project_name=project_name, text=text, userstories=userstories)

    return render_template('editing/create.html')


def init_taiga_api(host, username, password):
    api = TaigaAPI(
        host=host
    )
    api.auth(
        username=username,
        password=password
    )
    return api


def calc_min_level(lines):
    min_count_hash = float('inf')
    for line in lines:
        if not line.startswith('#'):
            continue
        count_hash = re.match(r'#+', line).end()
        min_count_hash = min(min_count_hash, count_hash)
    return min_count_hash


def get_linums(lines, target_level):
    linums = deque()
    for linum, line in enumerate(lines):
        if not line.startswith('#'):
            continue
        level = re.match(r'#+', line).end()
        if level == target_level:
            linums.append(linum)
    return linums


def create_us_list(lines, level, project):
    us_list = []
    status_name = 'New'
    status = project.us_statuses.get(name=status_name).id
    tag_name = 'team: dev'
    tags = {tag_name: project.list_tags()[tag_name]}

    linums_us = get_linums(lines, level)
    for idx, linum in enumerate(linums_us):
        us = defaultdict()
        us['title'] = lines[linum].strip('#').strip()
        us['status'] = status
        us['tags'] = tags
        linum_next = linums_us[idx + 1] if not idx == len(linums_us) - 1 else -1
        lines_descoped = lines[linum:linum_next]
        us['task_list'] = create_task_list(lines_descoped, level + 1)
        us_list.append(us)
    return us_list


def create_task_list(lines, level):
    task_list = []
    linums_task = get_linums(lines, level)
    for idx, linum in enumerate(linums_task):
        task = defaultdict()
        task['title'] = lines[linum].strip('#').strip()
        linum_next = linums_task[idx+1] if not idx == len(linums_task) - 1 else -1
        task['desc'] = ''.join(lines[linum + 1:linum_next])
        task_list.append(task)
    return task_list


def add_us_to_project(us_list, project):
    for us in us_list:
        us_obj = project.add_user_story(us['title'], status=us['status'], tags=us['tags'])
        for task in us['task_list']:
            us_obj.add_task(
                task['title'],
                project.task_statuses.get(name='New').id,
                description=task['desc'],
            )
