#!/usr/bin/env python3

import sys
import re
from taiga import TaigaAPI
from collections import deque, defaultdict
from configparser import ConfigParser


def init_taiga_api(host, username, password):
    api = TaigaAPI(
        host=host
    )
    api.auth(
        username=username,
        password=password
    )
    return api


def readfile_as_array(filename):
    f = open(filename, 'r')
    lines = []
    for line in f.readlines():
        lines.append(line)
    f.close()
    return lines


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


def calc_commit_line(lines):
    for linum, line in enumerate(lines):
        if re.match(r'--- commit line ---', line, re.IGNORECASE):
            return linum
    return len(lines)


def get_milestone(project, milestone_name):
    for milestone in project.list_milestones():
        if milestone.name == milestone_name:
            return milestone
    return None


def create_us_list(text, project, status_name, tag_name, milestone_name):
    lines = text.splitlines()
    level = calc_min_level(lines)
    commit_line = calc_commit_line(lines)
    status = project.us_statuses.get(name=status_name)
    tags = {tag_name: project.list_tags()[tag_name]}
    milestone = None
    if milestone_name != '':
        # Should handle error
        milestone = get_milestone(project, milestone_name)
    us_list = []
    task_status = project.task_statuses.get(name='New')
    point_dict = create_point_dict(project)
    linums_us = get_linums(lines, level)
    for idx, linum in enumerate(linums_us):
        us = defaultdict()
        us['title'] = lines[linum].strip('#').strip()

        if us['title'].startswith('#'):
            # the userstory already exists
            us['exists'] = True
            match_obj = re.match(r'#\d+', us['title'])
            us['id'] = match_obj.group().strip('#')
            # exclude us number from the title
            us['title'] = us['title'][match_obj.end():].strip()
        else:
            us['exists'] = False
        if milestone is not None and commit_line > linum:
            us['milestone'] = milestone.id
        else:
            us['milestone'] = None
        us['status_id'] = status.id
        us['tags'] = tags
        match_obj = re.search(r'\[\d+pt\]', us['title'])
        if match_obj:
            point_name = match_obj.group().strip('[pt]')
            # exclude [Xpt] from the title
            us['title'] = us['title'][:match_obj.start()].strip()
        else:
            point_name = '?'
        # TODO: Should throw an error if there is no point specified
        us['point'] = point_dict[point_name]
        linum_next = linums_us[idx + 1] if not idx == len(linums_us) - 1 else -1
        lines_descoped = lines[linum:linum_next]
        us['task_list'] = create_task_list(lines_descoped, level + 1, task_status.id)
        us_list.append(us)
    return us_list


def create_task_list(lines, level, status_id):
    task_list = []
    linums_task = get_linums(lines, level)
    for idx, linum in enumerate(linums_task):
        task = defaultdict()
        task['title'] = lines[linum].strip('#').strip()
        linum_next = linums_task[idx+1] if not idx == len(linums_task) - 1 else len(lines)
        task['status_id'] = status_id
        task['desc'] = '\n'.join(lines[linum + 1:linum_next])
        task_list.append(dict(task))
    return task_list


def add_us_to_project(us_list, project):
    for us in us_list:
        if us['exists']:
            # TODO: Should handle error
            us_obj = project.get_userstory_by_ref(us['id'])
            us_obj.subject = us['title']
            us_obj.status = us['status_id']
            us_obj.tags = us['tags']
            if us['milestone'] is not None:
                us_obj.milestone = us['milestone']
        else:
            if us['milestone'] is not None:
                us_obj = project.add_user_story(us['title'], status=us['status_id'], tags=us['tags'], milestone=us['milestone'])
            else:
                us_obj = project.add_user_story(us['title'], status=us['status_id'], tags=us['tags'])
        # FIXME: Should specify point to change
        key = next(iter(us_obj.points))
        us_obj.points[key] = us['point']
        us_obj.update()

        for task in us['task_list']:
            us_obj.add_task(
                task['title'],
                task['status_id'],
                description=task['desc'],
            )


def create_point_dict(project):
    point_dict = defaultdict()
    for point in project.list_points():
        point_dict[point.name] = point.id
    return point_dict


def convert_text(userstories):
    text_converted = ''
    for us in userstories:
        line = f'- {us["title"]}\n'
        text_converted += line
        for task in us['task_list']:
            line = f'\t- {task["title"]}\n'
            text_converted += line
    return text_converted


def main():
    config_parser = ConfigParser()
    config_parser.read('config.ini')
    config = config_parser['default']

    api = init_taiga_api(config.get('host'), config.get('username'), config.get('password'))
    project = api.projects.get_by_slug(config.get('project_name'))

    filename = sys.argv[1]
    text = readfile_as_array(filename)
    status_name = 'New'
    tag_name = 'team: dev'
    milestone_name = ''
    status = project.us_statuses.get(name=status_name).id
    tags = {tag_name: project.list_tags()[tag_name]}

    us_list = create_us_list(text, project, status, tags, milestone_name)

    add_us_to_project(us_list, project)


if __name__ == '__main__':
    main()
