from flask import Flask, render_template, url_for, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from config import SECRET_KEY, SQLALCHEMY_DATABASE_URI


app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.Text, nullable=False)
    password = db.Column(db.Text, nullable=False)
    requests = db.relationship('LeaveRequest', backref='user', lazy=True)
    print("change for git")

    def __repr__(self):
        return '<User %r>' % self.id


class LeaveRequest(db.Model):
    print("change for git")
    __tablename__ = 'leave_request'
    id = db.Column(db.Integer, primary_key=True)
    reason = db.Column(db.String(200), nullable=False)
    date_start = db.Column(db.DateTime, nullable=False)
    date_end = db.Column(db.DateTime, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow())
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)

    def __repr__(self):
        return '<LeaveRequest %r>' % self.id

#features added:
@app.route('/', methods=['POST', 'GET'])
def index():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect('/login')

    user_id = session.get('user_id')

    if request.method == 'POST':
        leave_reason = request.form['reason']
        leave_date_start_str = request.form['date_start']
        leave_date_end_str = request.form['date_end']
        try:
            leave_date_start = datetime.strptime(leave_date_start_str, '%Y-%m-%d')
            leave_date_end = datetime.strptime(leave_date_end_str, '%Y-%m-%d')
        except ValueError:
            return 'Please enter valid dates'

        requested_days = (leave_date_end - leave_date_start).days + 1

        year = leave_date_start.year
        existing_leaves = LeaveRequest.query.filter(
            LeaveRequest.user_id == user_id,
            db.extract('year', LeaveRequest.date_start) == year
        ).all()

        total_days_taken = sum([(lr.date_end - lr.date_start).days + 1 for lr in existing_leaves])

        if total_days_taken + requested_days > 10:
            return 'You cannot request leave for more than 10 days in a year.'

        two_months_later = datetime.today() + timedelta(days=60)
        if leave_date_start > two_months_later:
            return 'You cannot request leave more than two months in advance.'

        existing_leave = LeaveRequest.query.filter_by(
            user_id=user_id,
            date_start=leave_date_start
        ).first()

        if existing_leave:
            return 'You have already requested leave for this date.'

        new_leave = LeaveRequest(
            reason=leave_reason,
            date_start=leave_date_start,
            date_end=leave_date_end,
            user_id=user_id
        )

        try:
            db.session.add(new_leave)
            db.session.commit()
            return redirect('/')
        except Exception as e:
            print(f"Error: {e}")
            return 'There was an issue adding your leave request'

    else:
        leaves = LeaveRequest.query.order_by(LeaveRequest.date_created).all()
        return render_template('index.html', leaves=leaves)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        user_name = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(user_name=user_name, password=password).first()
        if user:
            session['logged_in'] = True
            session['user_id'] = user.user_id
            return redirect('/')
        else:
            return 'Invalid username or password'
    else:
        return render_template('login.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        user_name = request.form['username']
        password = request.form['password']
        new_user = User(user_name=user_name, password=password)

        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect('/')
        except Exception as e:
            print(f"Error: {e}")
            return 'There was an issue registering your account'
    else:
        return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    return redirect('/login')


#features added:
@app.route('/delete/<int:id>')
def delete(id):
    leave_to_delete = LeaveRequest.query.get_or_404(id)

    if leave_to_delete.user_id == session.get('user_id'):
        if datetime.utcnow() < leave_to_delete.date_start:
            try:
                db.session.delete(leave_to_delete)
                db.session.commit()
                return redirect('/')
            except:
                return 'There was an issue deleting your leave request'
        else:
            return 'You cannot delete a leave request that has already started or passed'
    else:
        return 'You do not have permission to delete this request'


if __name__ == '__main__':
    app.run(debug=True, port=5001)