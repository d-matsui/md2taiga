from flask import (
    Blueprint, flash, g, render_template, request
)
from md2taiga.auth import login_required

bp = Blueprint('editing', __name__, url_prefix='/editing')


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        text = request.form['text']
        error = None

        if not text:
            error = 'Markdown text is required.'

        if error is not None:
            flash(error)
        else:
            # TODO: use md2taiga-cli then render the output
            return render_template('editing/create.html', text=text)

    return render_template('editing/create.html')
