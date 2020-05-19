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
        if us['title'].startswith('#'):
            # the userstory already exists
            us['exists'] = True
            match_obj = re.match(r'#\d+', us['title'])
            us['id'] = match_obj.group().strip('#')
            us['title'] = us['title'][match_obj.end():].strip()
        else:
            us['exists'] = False
            us['status'] = status
            us['tags'] = tags
        match_obj = re.search(r'\[\d+pt\]', us['title'])
        if match_obj:
            point_name = match_obj.group().strip('[pt]')
        else:
            point_name = '?'
        us['point'] = find_point_id(project, point_name)
        # TODO: Should throw an error when the point is None
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
        task['desc'] = '\n'.join(lines[linum + 1:linum_next])
        task_list.append(task)
    return task_list


def add_us_to_project(us_list, project):
    for us in us_list:
        if us['exists']:
            # TODO: Should handle error
            us_obj = project.get_userstory_by_ref(us['id'])
            us_obj.subject = us['title']
        else:
            us_obj = project.add_user_story(us['title'], status=us['status'], tags=us['tags'])
        # FIXME: Should specify point to change
        key = next(iter(us_obj.points))
        us_obj.points[key] = us['point']
        us_obj.update()

        for task in us['task_list']:
            us_obj.add_task(
                task['title'],
                project.task_statuses.get(name='New').id,
                description=task['desc'],
            )


def find_point_id(project, name):
    for point in project.list_points():
        if point.name == name:
            return point.id
    return None


def main():
    config_parser = ConfigParser()
    config_parser.read('config.ini')
    config = config_parser['default']

    api = init_taiga_api(config.get('host'), config.get('username'), config.get('password'))
    project = api.projects.get_by_slug(config.get('project_name'))

    filename = sys.argv[1]
    lines = readfile_as_array(filename)
    level_us = calc_min_level(lines)
    us_list = create_us_list(lines, level_us, project)

    add_us_to_project(us_list, project)


if __name__ == '__main__':
    main()
