from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ---------------- Models ----------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    questions = db.relationship("Question", backref="quiz", cascade="all,delete")

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text)
    option1 = db.Column(db.String(150))
    option2 = db.Column(db.String(150))
    option3 = db.Column(db.String(150))
    option4 = db.Column(db.String(150))
    correct_answer = db.Column(db.String(150))
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- Routes ----------------
@app.route("/")
def home():
    quizzes = Quiz.query.all()
    return render_template("home.html", quizzes=quizzes)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        if User.query.filter_by(username=username).first():
            flash("Username already exists.")
            return redirect(url_for("register"))
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash("Registered successfully! Please log in.")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("home"))
        flash("Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/create", methods=["GET", "POST"])
@login_required
def create_quiz():
    if request.method == "POST":
        title = request.form["title"]
        desc = request.form["description"]
        quiz = Quiz(title=title, description=desc, created_by=current_user.id)
        db.session.add(quiz)
        db.session.commit()

        # Get questions dynamically
        q_texts = request.form.getlist("question_text")
        opts1 = request.form.getlist("option1")
        opts2 = request.form.getlist("option2")
        opts3 = request.form.getlist("option3")
        opts4 = request.form.getlist("option4")
        corrects = request.form.getlist("correct_answer")

        for i in range(len(q_texts)):
            q = Question(
                question_text=q_texts[i],
                option1=opts1[i],
                option2=opts2[i],
                option3=opts3[i],
                option4=opts4[i],
                correct_answer=corrects[i],
                quiz_id=quiz.id
            )
            db.session.add(q)
        db.session.commit()
        flash("Quiz created successfully!")
        return redirect(url_for("home"))

    return render_template("create_quiz.html")

@app.route("/quiz/<int:quiz_id>", methods=["GET", "POST"])
def take_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if request.method == "POST":
        score = 0
        for q in quiz.questions:
            ans = request.form.get(str(q.id))
            if ans == q.correct_answer:
                score += 1
        return render_template("results.html", quiz=quiz, score=score)
    return render_template("take_quiz.html", quiz=quiz)

# Initialize DB
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=False)
