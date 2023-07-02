from flask_login import UserMixin

from app import db, login_manager, bcrypt

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True)
    password_hash = db.Column(db.String(100))
    account_type = db.Column(db.String(20))
    
    created_tasks = db.relationship('Task', backref='creator', lazy='dynamic')

    solved_tasks = db.relationship(
        'Task',
        secondary='solved_tasks',
        backref=db.backref('solvers', lazy='dynamic')
    )
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def verify_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    description = db.Column(db.Text)
    inputs = db.Column(db.Text)
    outputs = db.Column(db.Text)
    hidden_inputs = db.Column(db.Text)
    hidden_outputs = db.Column(db.Text)

    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f"<Task {self.id}>"


class SolvedTasks(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), primary_key=True)


@login_manager.user_loader
def load_user(username):
    return db.session.get(User, username)