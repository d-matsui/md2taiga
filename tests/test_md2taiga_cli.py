import pytest
import md2taiga.md2taiga_cli as md2taiga_cli
from collections import deque
import taiga.exceptions
from pprint import pprint


def test_fails_init_taiga_api_with_no_host():
    host = ''
    username = 'user'
    password = 'pass'

    with pytest.raises(taiga.exceptions.TaigaRestException) as e:
        md2taiga_cli.init_taiga_api(host, username, password)
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


def test_get_linums():
    lines = [
        '# US',
        '## Task',
        '### Description',
        '# US',
        '## Task',
        '### Description'
    ]
    assert md2taiga_cli.get_linums(lines, 1) == deque([0, 3])
    assert md2taiga_cli.get_linums(lines, 2) == deque([1, 4])
    assert md2taiga_cli.get_linums(lines, 3) == deque([2, 5])


def test_calc_commit_line():
    lines = [
        '# US',
        '## Task',
        '### Description',
        '--- commit line ---',
        '# US',
        '## Task',
        '### Description'
    ]
    assert md2taiga_cli.calc_commit_line(lines) == 3

    lines = [
        '# US',
        '## Task',
        '### Description',
        '# US',
        '## Task',
        '### Description'
    ]
    assert md2taiga_cli.calc_commit_line(lines) == len(lines)


def test_create_task_list():
    task_list = [
        {'title': 'Task1', 'status_id': 0, 'desc': '### Description1\n#### TODO'},
        {'title': 'Task2', 'status_id': 0, 'desc': '### Description2\n#### TODO'}
    ]
    lines = [
        '# US',
        '## Task1',
        '### Description1',
        '#### TODO',
        '## Task2',
        '### Description2',
        '#### TODO'
    ]
    assert md2taiga_cli.create_task_list(lines, 2, 0) == task_list


# --- TODO ---
# test_init_taiga_api()
# test_get_milestone()
