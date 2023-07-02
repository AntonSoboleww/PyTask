from flask import render_template, redirect, request, url_for, jsonify
from flask_login import login_required, logout_user, current_user, login_user

from app import app, db, csrf
from app.models import *
from app.forms import *

# Страница общего дашборда со списком задач
@app.route('/')
@app.route('/home')
@app.route('/dashboard')
@login_required
def dashboard():
    tasks = Task.query.all()
    return render_template('dashboard.html', tasks=tasks)


# Страница создания задачи
@app.route('/create_task', methods=['GET'])
@login_required
@csrf.exempt
def create_task():
    return render_template('create_task.html')


@app.route('/edit_task/<int:task_id>', methods=['GET'])
@login_required
@csrf.exempt
def edit_task(task_id):
    task = db.session.get(Task, task_id)
    if (not task or current_user.id != task.creator_id) and (current_user.account_type not in ['admin']):
        return redirect(url_for('dashboard'))

    return render_template('edit_task.html', task=task)


# Страница выполнения и проверки задачи
@app.route('/task/<int:task_id>', methods=['GET'])
@login_required
@csrf.exempt
def solve_task(task_id):
    task = db.session.get(Task, task_id)

    return render_template('solve_task.html', task=task)


@app.route('/admin_panel', methods=['GET'])
@login_required
@csrf.exempt
def admin_panel():
    if current_user.account_type != 'admin':
        return redirect(url_for('dashboard'))

    return render_template('admin_panel.html')
    

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        username = request.json.get('username')
        password = request.json.get('password')
        confirm_password = request.json.get('confirm_password')

        if not username or not password or not confirm_password:
            return jsonify(error="Please enter both username and password.")

        user = User.query.filter_by(username=username).first()
        if user:
            return jsonify(error="Username already exists. Please choose a different username.")
        
        if password != confirm_password:
            return jsonify(error="Пароли не совпадают.")

        user = User(username=username, account_type='student')
        user.password = password
        db.session.add(user)
        db.session.commit()

        return jsonify(redirect_url=url_for('dashboard'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        username = request.json.get('username')
        password = request.json.get('password')

        user = User.query.filter_by(username=username).first()
        if not user or not user.verify_password(password):
            return jsonify(error="Имя пользователя или пароль введены неверно.")
        else:
            login_user(user)
            return jsonify(redirect_url=url_for('dashboard'))
    
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('dashboard'))