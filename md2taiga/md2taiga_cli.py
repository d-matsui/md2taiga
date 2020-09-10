#!/usr/bin/env python3

import sys
from configparser import ConfigParser
import re
from taiga import TaigaAPI
from collections import deque, defaultdict


def setup_taiga_api(hostname, username, password):
    api = TaigaAPI(
        host=hostname
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
    min_level = float('inf')
    for line in lines:
        if not line.startswith('#'):
            continue
        level = re.match(r'#+', line).end()
        min_level = min(min_level, level)
    return min_level


def get_line_numbers_by_level(lines, target_level):
    line_numbers = deque()
    for line_num, line in enumerate(lines):
        if not line.startswith('#'):
            continue
        level = re.match(r'#+', line).end()
        if level == target_level:
            line_numbers.append(line_num)
    return line_numbers


def get_line_num_of_commit_line(lines):
    for line_num, line in enumerate(lines):
        if re.match(r'--- commit line ---', line, re.IGNORECASE):
            return line_num
    return len(lines)


def find_milestone_by_name(project, milestone_name):
    if milestone_name != '':
        for milestone in project.list_milestones():
            if milestone.name == milestone_name:
                return milestone
    return None


def create_us_list(text, project, status_name, tag_name, milestone_name):
    lines = text.splitlines()
    level_us = calc_min_level(lines)
    level_task = level_us + 1
    commit_line = get_line_num_of_commit_line(lines)

    # TODO: Error handling
    us_status = project.us_statuses.get(name=status_name)
    tags = {tag_name: project.list_tags()[tag_name]}
    milestone = find_milestone_by_name(project, milestone_name)
    task_status = project.task_statuses.get(name='New')

    point_dict = create_point_dict(project)
    role_dict = create_role_dict(project)
    line_numbers_us = get_line_numbers_by_level(lines, level_us)

    us_list = []
    for idx, line_num in enumerate(line_numbers_us):
        line_num_next = line_numbers_us[idx + 1] if not idx == len(line_numbers_us) - 1 else -1
        us = create_us(lines, line_num, line_num_next, milestone, us_status, tags, commit_line, task_status, point_dict, role_dict, level_task)
        us_list.append(us)
    return us_list


def create_us(lines, line_num, line_num_next, milestone, us_status, tags, commit_line, task_status, point_dict, role_dict, level_task):
    us = defaultdict()

    # Exclude '#' prefix from the us title
    us['title'] = lines[line_num].strip('#').strip()

    if us['title'].startswith('#'):
        us['id'] = get_id_prefix(us['title'])
        us['title'] = extract_num_prefix(us['title'])
    else:
        us['id'] = None

    if milestone is not None and commit_line > line_num:
        us['milestone_id'] = milestone.id
    else:
        us['milestone_id'] = None

    us['status_id'] = us_status.id
    us['tags'] = tags

    match_obj = re.search(r'\[\d+pt\]', us['title'])
    if match_obj:
        point_name = match_obj.group().strip('[pt]')
        # Exclude '[Xpt]' from the us title
        us['title'] = us['title'][:match_obj.start()].strip()
    else:
        point_name = '?'
    # TODO: Error handling when there is no specified point
    us['point_id'] = point_dict[point_name]
    role_name = next(iter(role_dict))
    # uncomment next line if you want to Specify role
    # role_name = 'DevOps'
    us['role_id'] = role_dict[role_name]

    lines_clipped = lines[line_num:line_num_next]
    us['task_list'] = create_task_list(lines_clipped, level_task, task_status.id, us['id'])

    return dict(us)


def extract_num_prefix(title):
    match_obj = re.match(r'#\d+', title)
    title_extracted = title[match_obj.end():].strip()
    return title_extracted


def get_id_prefix(title):
    match_obj = re.match(r'#\d+', title)
    id = match_obj.group().strip('#')
    return id


def create_task_list(lines, level, status_id, us_id):
    task_list = []
    line_nums_task = get_line_numbers_by_level(lines, level)
    for idx, line_num in enumerate(line_nums_task):
        line_num_next = line_nums_task[idx+1] if not idx == len(line_nums_task) - 1 else len(lines)
        task = create_task(lines, line_num, line_num_next, status_id, us_id)
        task_list.append(task)
    return task_list


def create_task(lines, line_num, line_num_next, status_id, us_id):
    task = defaultdict()
    # Exclude '#' prefix from the task title
    task['title'] = lines[line_num].strip('#').strip()
    task['status_id'] = status_id
    task['desc'] = '\n'.join(lines[line_num + 1:line_num_next])

    if us_id is not None and task['title'].startswith('#'):
        task['id'] = get_id_prefix(task['title'])
        task['title'] = extract_num_prefix(task['title'])
    else:
        task['id'] = None
    return dict(task)


def add_us_to_project(us_list, project):
    for us in us_list:
        if us['id'] is not None:
            # TODO: Error handling
            us_obj = project.get_userstory_by_ref(us['id'])
            us_obj.subject = us['title']
            us_obj.status = us['status_id']
            us_obj.tags = us['tags']
            if us['milestone_id'] is not None:
                us_obj.milestone = us['milestone_id']
        else:
            if us['milestone_id'] is not None:
                us_obj = project.add_user_story(us['title'], status=us['status_id'], tags=us['tags'], milestone=us['milestone_id'])
            else:
                us_obj = project.add_user_story(us['title'], status=us['status_id'], tags=us['tags'])
        us_obj.points[us['role_id']] = us['point_id']
        us_obj.update()

        for task in us['task_list']:
            if task['id'] is not None:
                task_obj = project.get_task_by_ref(task['id'])
                task_obj.subject = task['title']
                task_obj.status = task['status_id']
                task_obj.description = task['desc']
                task_obj.update()
            else:
                us_obj.add_task(
                    task['title'],
                    task['status_id'],
                    description=task['desc'],
                )


def create_point_dict(project):
    point_dict = defaultdict()
    for point in project.list_points():
        point_dict[point.name] = point.id
    return dict(point_dict)


def create_role_dict(project):
    role_dict = defaultdict()
    for role in project.list_roles():
        role_dict[role.name] = role.id
    return dict(role_dict)


def convert_text(us_list):
    text_converted = ''
    for us in us_list:
        line = f'- {us["title"]}\n'
        text_converted += line
        for task in us['task_list']:
            line = f'\t- {task["title"]}\n'
            text_converted += line
    return text_converted


# def main():
#     config_parser = ConfigParser()
#     config_parser.read('config.ini')
#     config = config_parser['default']

#     api = init_taiga_api(config.get('host'), config.get('username'), config.get('password'))
#     project = api.projects.get_by_slug(config.get('project_name'))

#     filename = sys.argv[1]
#     text = readfile_as_array(filename)
#     status_name = 'New'
#     tag_name = 'team: dev'
#     milestone_name = ''
#     status = project.us_statuses.get(name=status_name).id
#     tags = {tag_name: project.list_tags()[tag_name]}

#     us_list = create_us_list(text, project, status, tags, milestone_name)

#     add_us_to_project(us_list, project)


# if __name__ == '__main__':
#     main()
