import pytest
import md2taiga.md2taiga_cli as md2taiga_cli
from collections import deque
import taiga.exceptions
from pprint import pprint


def test_fails_setup_taiga_api_with_no_host():
    host = ''
    username = 'user'
    password = 'pass'

    with pytest.raises(taiga.exceptions.TaigaRestException) as e:
        md2taiga_cli.setup_taiga_api(host, username, password)
    assert str(e.value) == 'NETWORK ERROR'


def test_calc_min_level():
    lines = [
        '# US',
        '## Task',
        '### Description'
    ]
    level = md2taiga_cli.calc_min_level(lines)
    assert level == 1

    lines = [
        '### US',
        '#### Task',
        '##### Description'
    ]
    level = md2taiga_cli.calc_min_level(lines)
    assert level == 3


def test_get_line_numbers_by_level():
    lines = [
        '# US',
        '## Task',
        '### Description',
        '# US',
        '## Task',
        '### Description'
    ]
    assert md2taiga_cli.get_line_numbers_by_level(lines, 1) == deque([0, 3])
    assert md2taiga_cli.get_line_numbers_by_level(lines, 2) == deque([1, 4])
    assert md2taiga_cli.get_line_numbers_by_level(lines, 3) == deque([2, 5])


def test_get_line_num_of_commit_line():
    lines = [
        '# US',
        '## Task',
        '### Description',
        '--- commit line ---',
        '# US',
        '## Task',
        '### Description'
    ]
    assert md2taiga_cli.get_line_num_of_commit_line(lines) == 3

    lines = [
        '# US',
        '## Task',
        '### Description',
        '# US',
        '## Task',
        '### Description'
    ]
    assert md2taiga_cli.get_line_num_of_commit_line(lines) == len(lines)


def test_create_task_list():
    task_list = [
        {'title': 'Task1', 'status_id': 0, 'desc': '### Description\n#### TODO'},
        {'title': 'Task2', 'status_id': 0, 'desc': '### Description\n#### TODO'}
    ]
    lines = [
        '# US',
        '## Task1',
        '### Description',
        '#### TODO',
        '## Task2',
        '### Description',
        '#### TODO'
    ]
    assert md2taiga_cli.create_task_list(lines, 2, 0) == task_list


def test_convert_text():
    us_list = [{'title': 'US1',
                'task_list': [{'title': 'Task1', 'status_id': 0, 'desc': '### Description\n#### TODO'},
                              {'title': 'Task2', 'status_id': 0, 'desc': '### Description\n#### TODO'}]},
               {'title': 'US2',
                'task_list': [{'title': 'Task1', 'status_id': 0, 'desc': '### Description\n#### TODO'},
                              {'title': 'Task2', 'status_id': 0, 'desc': '### Description\n#### TODO'}]}]
    text_converted = '- US1\n\t- Task1\n\t- Task2\n- US2\n\t- Task1\n\t- Task2\n'

    assert md2taiga_cli.convert_text(us_list) == text_converted


# --- TODO ---
# def test_init_taiga_api()
# def test_get_milestone()
# def test_add_us_to_project()
# def test_create_point_dict()
