import subprocess

from flask import jsonify, request, abort
from flask_login import login_required, current_user

from app import app, db, csrf
from app.models import User, Task
from app.utils import check_code

@app.route('/api/user', methods=['GET'])
@csrf.exempt
@login_required
def get_users():
    users = User.query.all()
    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'username': user.username,
            'account_type': user.account_type
        })
    return jsonify(users_data), 200

@app.route('/api/user', methods=['POST'])
@csrf.exempt
@login_required
def create_user():
    if current_user.account_type != 'admin':
        abort(403)

    data = request.get_json()
    username = data['username']
    password = data['password']
    account_type = data['account_type']
    user = User(username=username, account_type=account_type)
    user.password = password
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User created successfully'}), 200

@app.route('/api/user/<int:user_id>', methods=['PUT'])
@csrf.exempt
@login_required
def update_user(user_id):
    if current_user.account_type != 'admin':
        abort(403)

    data = request.get_json()
    account_type = data['account_type']
    user = User.query.get(user_id)
    user.account_type = account_type
    db.session.commit()
    return jsonify({'message': 'User updated successfully'}), 200

@app.route('/api/user/<int:user_id>/password', methods=['PUT'])
@csrf.exempt
@login_required
def update_user_password(user_id):
    if current_user.account_type != 'admin':
        abort(403)

    data = request.get_json()
    password = data['password']
    user = User.query.get(user_id)
    user.set_password(password)
    db.session.commit()
    return jsonify({'message': 'User password updated successfully'}), 200

@app.route('/api/user/<int:user_id>', methods=['DELETE'])
@csrf.exempt
@login_required
def delete_user(user_id):
    if current_user.account_type != 'admin':
        abort(403)

    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'}), 200

@app.route('/api/task/<int:task_id>/solve', methods=['POST'])
@csrf.exempt
@login_required
def solve_task_api(task_id):
    task = db.session.get(Task, task_id)
    
    data = request.get_json()
    
    user_code = data['code']
    inputs = task.inputs.split('\n')
    outputs = task.outputs.split('\n')
    all_errors = len(inputs)
    tasks_input = inputs
    tasks_output = outputs

    if task.hidden_inputs != '':
        hidden_inputs = task.hidden_inputs.split('\n')
        hidden_outputs = task.hidden_outputs.split('\n')
        all_errors += len(hidden_inputs)
        tasks_input += hidden_inputs
        tasks_output += hidden_outputs
    else:
        hidden_inputs = None
        hidden_outputs = None

    results = []
    allowed_libraries = ['random']
    disabled_functions = ['exec', 'eval', 'compile', 'execfile']

    has_error = False
    has_exception = False
    excep = ''

    has_err_solution = False
    wait_solution = ''
    answer_solution = ''

    solve = 0

    for i, input_line in enumerate(tasks_input):
        input_data = input_line.split()
        output_data = (tasks_output)[i].replace('\r', '')

        try:
            check_code(user_code, allowed_libraries, disabled_functions)

            process = subprocess.run(['python', '-u', '-c', user_code],
                                     input='\n'.join(input_data),
                                     capture_output=True,
                                     text=True,
                                     universal_newlines=True,
                                     timeout=5)

            stdout = process.stdout.strip()
            stderr = process.stderr

            if stderr:
                # Ошибка
                results.append(stderr)
                has_error = True
                break
            elif stdout == output_data:
                # Верно
                results.append(stdout)
            else:
                # Неверно
                results.append(stdout)
                answer_solution = input_line
                wait_solution = output_data
                has_err_solution = True
                break
        except subprocess.TimeoutExpired:
            excep = 'TimeoutExpired'
            has_exception = True
            break
        except Exception as e:
            excep = e
            has_exception = True
            break

        solve += 1

    if has_err_solution == True:
        return jsonify(f"Неверно! Решено {solve} из {all_errors}\nВходные данные: {answer_solution}\nОжидалось: {wait_solution}\nТвой ответ: {results[-1]}"), 200
    elif has_error == True:
        return jsonify(f"Ошибка: {results[-1]}"), 200
    elif has_exception == True:
        if excep == 'TimeoutExpired':
            return jsonify(f"Ошибка: Превышен лимит времени выполнения кода (5 секунд)"), 200
        else:
            return jsonify(f"Ошибка: {excep}"), 200
    else:
        user = db.session.get(User, current_user.id)
        user.solved_tasks.append(task)
        db.session.commit()
        return jsonify('Всё решено верно!'), 200
    
    
@app.route('/api/create_task', methods=['POST'])
@login_required
@csrf.exempt
def create_task_api():
    if current_user.account_type not in ['teacher', 'admin']:
        return jsonify({'message': 'Unauthorized'}), 401

    print(request.get_json())
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    inputs = data.get('inputs')
    outputs = data.get('outputs')
    hidden_inputs = data.get('hidden_inputs')
    hidden_outputs = data.get('hidden_outputs')

    if (inputs and not outputs) or (outputs and not inputs):
        return jsonify({'message': 'If inputs are provided, outputs are required and vice versa.'}), 400

    if (hidden_inputs and not hidden_outputs) or (hidden_outputs and not hidden_inputs):
        return jsonify({'message': 'If hidden inputs are provided, hidden outputs are required and vice versa.'}), 400

    task = Task(
        title = title,
        description = description,
        inputs = inputs,
        outputs = outputs,
        hidden_inputs = hidden_inputs,
        hidden_outputs = hidden_outputs
    )
        
    task.creator_id = current_user.id
    
    db.session.add(task)
    db.session.commit()

    return jsonify({'message': 'Task updated successfully'}), 200
    
    
@app.route('/api/edit_task/<int:task_id>', methods=['UPDATE'])
@login_required
@csrf.exempt
def edit_task_api(task_id):
    task = db.session.get(Task, task_id)
    
    if (not task or current_user.id != task.creator_id) and (current_user.account_type not in ['admin']):
        return jsonify({'message': 'Unauthorized'}), 401

    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    inputs = data.get('inputs')
    outputs = data.get('outputs')
    hidden_inputs = data.get('hidden_inputs')
    hidden_outputs = data.get('hidden_outputs')

    if (inputs and not outputs) or (outputs and not inputs):
        return jsonify({'message': 'If inputs are provided, outputs are required and vice versa.'}), 400

    if (hidden_inputs and not hidden_outputs) or (hidden_outputs and not hidden_inputs):
        return jsonify({'message': 'If hidden inputs are provided, hidden outputs are required and vice versa.'}), 400

    task.title = title
    task.description = description
    task.inputs = inputs
    task.outputs = outputs
    task.hidden_inputs = hidden_inputs
    task.hidden_outputs = hidden_outputs

    db.session.commit()

    return jsonify({'message': 'Task updated successfully'}), 200
    
    
@app.route('/api/delete_task/<int:task_id>', methods=['DELETE'])
@login_required
@csrf.exempt
def delete_task_api(task_id):
    task = db.session.get(Task, task_id)

    if (not task or current_user.id != task.creator_id) and (current_user.account_type not in ['admin']):
        return jsonify({'message': 'Unauthorized'}), 401

    db.session.delete(task)
    db.session.commit()

    return jsonify({'message': 'Task deleted successfully'}), 200
