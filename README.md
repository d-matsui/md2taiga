# md2taiga

A web application for creating user stories on Taiga.io from markdown text

## Getting Started

You can run this app in your local environment.

``` shell
git clone git@github.com:d-matsui/md2taiga.git
cd md2taiga
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
source ./export.sh
python3 -m flask run
```

## Test

```shell
python3 -m pytest -v
```

## Examples of markdown text

You can add multiple subtasks for each user story.

Note that the level of the user story must be just one less than the level of the subtask.

``` markdown
# User Story Title
## Subtask Title
### Description of the subtask

### Definition of completion the subtask

### Demo

## Subtask Title
### Description of the subtask

### Definition of completion the subtask

### Demo

# User Story Title
## Subtask Title
### Description of the subtask

### Definition of completion the subtask

### Demo

## Subtask Title
### Description of the subtask

### Definition of completion the subtask

### Demo

```

You can specify the user story point as follows.

``` markdown
### User Story Title [Xpt]
#### Subtask Title
##### Description of the subtask

##### Definition of completion the subtask

##### Demo
```

You can overwrite the existing user story and task by specifying their id.

``` markdown
## #USID User Story Title [Xpt]
### #TASKID Subtask Title
#### Description of the subtask

#### Definition of completion the subtask

#### Demo
```

## Screen-shots

![md2taiga](md2taiga/static/md2taiga-example.png)

![md2taiga](md2taiga/static/taiga-example.png)
