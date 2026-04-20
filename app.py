from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "secret123"

# DATABASE CONFIG
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ================= MODELS =================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    acc_no = db.Column(db.Integer)
    balance = db.Column(db.Float)
    type = db.Column(db.String(20))
    user_id = db.Column(db.Integer)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    acc_no = db.Column(db.Integer)
    type = db.Column(db.String(20))
    amount = db.Column(db.Float)
    user_id = db.Column(db.Integer)


# ================= HELPER =================

def is_logged_in():
    return 'user_id' in session


# ================= AUTH =================

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(
            username=request.form['username'],
            password=request.form['password']
        ).first()

        if user:
            session['user_id'] = user.id
            flash("Login successful!", "success")
            return redirect('/dashboard')
        else:
            flash("Invalid username or password!", "error")

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        existing = User.query.filter_by(username=request.form['username']).first()

        if existing:
            flash("Username already exists!", "error")
            return redirect('/signup')

        new_user = User(
            username=request.form['username'],
            password=request.form['password']
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Signup successful! Please login.", "success")
        return redirect('/')

    return render_template('signup.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ================= DASHBOARD =================

@app.route('/dashboard')
def dashboard():
    if not is_logged_in():
        return redirect('/')

    accounts = Account.query.filter_by(user_id=session['user_id']).all()
    return render_template('dashboard.html', accounts=accounts)


# ================= CREATE ACCOUNT =================

@app.route('/create', methods=['GET', 'POST'])
def create():
    if not is_logged_in():
        return redirect('/')

    if request.method == 'POST':
        acc = Account(
            acc_no=int(request.form['acc_no']),
            balance=float(request.form['balance']),
            type=request.form['type'],
            user_id=session['user_id']
        )

        db.session.add(acc)
        db.session.commit()

        flash("Account created successfully!", "success")
        return redirect('/dashboard')

    return render_template('create.html')


# ================= DEPOSIT =================

@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if not is_logged_in():
        return redirect('/')

    if request.method == 'POST':
        acc = Account.query.filter_by(
            acc_no=request.form['acc_no'],
            user_id=session['user_id']
        ).first()

        if not acc:
            flash("Account not found!", "error")
            return redirect('/deposit')

        amount = float(request.form['amount'])
        acc.balance += amount

        db.session.add(Transaction(
            acc_no=acc.acc_no,
            type="Deposit",
            amount=amount,
            user_id=session['user_id']
        ))

        db.session.commit()

        flash("Deposit successful!", "success")
        return redirect('/dashboard')

    return render_template('deposit.html')


# ================= WITHDRAW =================

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if not is_logged_in():
        return redirect('/')

    if request.method == 'POST':
        acc = Account.query.filter_by(
            acc_no=request.form['acc_no'],
            user_id=session['user_id']
        ).first()

        if not acc:
            flash("Account not found!", "error")
            return redirect('/withdraw')

        amount = float(request.form['amount'])

        # Savings Rule
        if acc.type == "savings" and acc.balance - amount < 500:
            flash("Minimum balance ₹500 required!", "error")
            return redirect('/withdraw')

        # Checking Rule
        if acc.type == "checking" and acc.balance - amount < -1000:
            flash("Overdraft limit ₹1000 exceeded!", "error")
            return redirect('/withdraw')

        acc.balance -= amount

        db.session.add(Transaction(
            acc_no=acc.acc_no,
            type="Withdraw",
            amount=amount,
            user_id=session['user_id']
        ))

        db.session.commit()

        flash("Withdrawal successful!", "success")
        return redirect('/dashboard')

    return render_template('withdraw.html')


# ================= HISTORY =================

@app.route('/history')
def history():
    if not is_logged_in():
        return redirect('/')

    transactions = Transaction.query.filter_by(user_id=session['user_id']).all()
    return render_template('history.html', transactions=transactions)


# ================= INIT =================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)