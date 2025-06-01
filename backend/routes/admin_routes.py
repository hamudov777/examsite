from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Exam, Quiz, Test, Answer
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
            flash("Доступ только для администратора.", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_view

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    return render_template('admin/dashboard.html')

# Экзамены
@admin_bp.route('/exams')
@login_required
@admin_required
def exams_list():
    exams = Exam.query.all()
    return render_template('admin/exam_list.html', exams=exams)

@admin_bp.route('/exams/add', methods=['GET', 'POST'])
@login_required
@admin_required
def exam_add():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description')
        date_str = request.form.get('date')
        date_obj = None
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                flash('Неверный формат даты.', 'danger')
                return render_template('admin/exam_add.html')
        exam = Exam(title=title, description=description, date=date_obj)
        db.session.add(exam)
        db.session.flush()
        questions_found = False
        for key in request.form:
            if key.startswith('questions[') and key.endswith('][text]'):
                questions_found = True
                qnum = key.split('[')[1].split(']')[0]
                qtext = request.form[key]
                correct = request.form.get(f'questions[{qnum}][correct]')
                answers = [request.form.get(f'questions[{qnum}][answers][{i}]') for i in range(4)]
                if not qtext.strip() or not all(a.strip() for a in answers) or correct is None:
                    flash('Заполните все поля и выберите правильный ответ для каждого вопроса.', 'danger')
                    return render_template('admin/exam_add.html')
                test = Test(question=qtext, exam_id=exam.id)
                db.session.add(test)
                db.session.flush()
                for i, ans in enumerate(answers):
                    answer = Answer(text=ans, is_correct=(str(i)==correct), test_id=test.id)
                    db.session.add(answer)
        if not questions_found:
            flash('Добавьте хотя бы один вопрос.', 'danger')
            return render_template('admin/exam_add.html')
        db.session.commit()
        flash('Экзамен добавлен!', 'success')
        return redirect(url_for('admin.exams_list'))
    return render_template('admin/exam_add.html')

@admin_bp.route('/exams/<int:exam_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def exam_edit(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if request.method == 'POST':
        exam.title = request.form['title']
        exam.description = request.form.get('description')
        date_str = request.form.get('date')
        exam.date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else None
        for test in exam.tests:
            for answer in getattr(test, 'answers', []):
                db.session.delete(answer)
            db.session.delete(test)
        db.session.flush()
        questions_found = False
        for key in request.form:
            if key.startswith('questions[') and key.endswith('][text]'):
                questions_found = True
                qnum = key.split('[')[1].split(']')[0]
                qtext = request.form[key]
                correct = request.form.get(f'questions[{qnum}][correct]')
                answers = [request.form.get(f'questions[{qnum}][answers][{i}]') for i in range(4)]
                if not qtext.strip() or not all(a.strip() for a in answers) or correct is None:
                    flash('Заполните все поля и выберите правильный ответ для каждого вопроса.', 'danger')
                    questions = []
                    for key2 in request.form:
                        if key2.startswith('questions[') and key2.endswith('][text]'):
                            qnum2 = key2.split('[')[1].split(']')[0]
                            qtext2 = request.form[key2]
                            correct2 = request.form.get(f'questions[{qnum2}][correct]')
                            answers2 = [request.form.get(f'questions[{qnum2}][answers][{i}]') for i in range(4)]
                            questions.append({'text': qtext2, 'answers': answers2, 'correct': int(correct2) if correct2 else 0})
                    return render_template('admin/exam_edit.html', exam=exam, questions=questions)
                test = Test(question=qtext, exam_id=exam.id)
                db.session.add(test)
                db.session.flush()
                for i, ans in enumerate(answers):
                    answer = Answer(text=ans, is_correct=(str(i)==correct), test_id=test.id)
                    db.session.add(answer)
        if not questions_found:
            flash('Добавьте хотя бы один вопрос.', 'danger')
            return render_template('admin/exam_edit.html', exam=exam, questions=[])
        db.session.commit()
        flash('Экзамен обновлён!', 'success')
        return redirect(url_for('admin.exams_list'))
    questions = []
    for test in exam.tests:
        q_answers = sorted(test.answers, key=lambda a: a.id)
        questions.append({
            'text': test.question,
            'answers': [a.text for a in q_answers],
            'correct': next((i for i, a in enumerate(q_answers) if a.is_correct), 0)
        })
    return render_template('admin/exam_edit.html', exam=exam, questions=questions)

@admin_bp.route('/exams/<int:exam_id>/delete', methods=['POST'])
@login_required
@admin_required
def exam_delete(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    db.session.delete(exam)
    db.session.commit()
    flash('Экзамен удален!', 'success')
    return redirect(url_for('admin.exams_list'))

# Тесты (Quiz)
@admin_bp.route('/tests')
@login_required
@admin_required
def tests_list():
    quizzes = Quiz.query.all()
    return render_template('admin/test_list.html', quizzes=quizzes)

@admin_bp.route('/tests/add', methods=['GET', 'POST'])
@login_required
@admin_required
def test_add():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description')
        date_str = request.form.get('date')
        date_obj = None
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                flash('Неверный формат даты.', 'danger')
                return render_template('admin/test_add.html')
        quiz = Quiz(title=title, description=description, date=date_obj)
        db.session.add(quiz)
        db.session.flush()
        questions_found = False
        for key in request.form:
            if key.startswith('questions[') and key.endswith('][text]'):
                questions_found = True
                qnum = key.split('[')[1].split(']')[0]
                qtext = request.form[key]
                correct = request.form.get(f'questions[{qnum}][correct]')
                answers = [request.form.get(f'questions[{qnum}][answers][{i}]') for i in range(4)]
                if not qtext.strip() or not all(a.strip() for a in answers) or correct is None:
                    flash('Заполните все поля и выберите правильный ответ для каждого вопроса.', 'danger')
                    return render_template('admin/test_add.html')
                test = Test(question=qtext, quiz_id=quiz.id)
                db.session.add(test)
                db.session.flush()
                for i, ans in enumerate(answers):
                    answer = Answer(text=ans, is_correct=(str(i) == correct), test_id=test.id)
                    db.session.add(answer)
        if not questions_found:
            flash('Добавьте хотя бы один вопрос.', 'danger')
            return render_template('admin/test_add.html')
        db.session.commit()
        flash('Тест добавлен!', 'success')
        return redirect(url_for('admin.tests_list'))
    return render_template('admin/test_add.html')

@admin_bp.route('/tests/<int:quiz_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def test_edit(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if request.method == 'POST':
        quiz.title = request.form['title']
        quiz.description = request.form.get('description')
        date_str = request.form.get('date')
        quiz.date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else None
        # Удаляем старые вопросы и ответы
        for test in quiz.tests:
            for answer in test.answers:
                db.session.delete(answer)
            db.session.delete(test)
        db.session.flush()
        questions_found = False
        for key in request.form:
            if key.startswith('questions[') and key.endswith('][text]'):
                questions_found = True
                qnum = key.split('[')[1].split(']')[0]
                qtext = request.form[key]
                correct = request.form.get(f'questions[{qnum}][correct]')
                answers = [request.form.get(f'questions[{qnum}][answers][{i}]') for i in range(4)]
                if not qtext.strip() or not all(a.strip() for a in answers) or correct is None:
                    flash('Заполните все поля и выберите правильный ответ для каждого вопроса.', 'danger')
                    questions = []
                    for key2 in request.form:
                        if key2.startswith('questions[') and key2.endswith('][text]'):
                            qnum2 = key2.split('[')[1].split(']')[0]
                            qtext2 = request.form[key2]
                            correct2 = request.form.get(f'questions[{qnum2}][correct]')
                            answers2 = [request.form.get(f'questions[{qnum2}][answers][{i}]') for i in range(4)]
                            questions.append({'text': qtext2, 'answers': answers2, 'correct': int(correct2) if correct2 else 0})
                    return render_template('admin/test_edit.html', quiz=quiz, questions=questions)
                test = Test(question=qtext, quiz_id=quiz.id)
                db.session.add(test)
                db.session.flush()
                for i, ans in enumerate(answers):
                    answer = Answer(text=ans, is_correct=(str(i) == correct), test_id=test.id)
                    db.session.add(answer)
        if not questions_found:
            flash('Добавьте хотя бы один вопрос.', 'danger')
            return render_template('admin/test_edit.html', quiz=quiz, questions=[])
        db.session.commit()
        flash('Тест обновлён!', 'success')
        return redirect(url_for('admin.tests_list'))
    # Для отображения вопросов при редактировании
    questions = []
    for test in quiz.tests:
        q_answers = sorted(test.answers, key=lambda a: a.id)
        questions.append({
            'text': test.question,
            'answers': [a.text for a in q_answers],
            'correct': next((i for i, a in enumerate(q_answers) if a.is_correct), 0)
        })
    return render_template('admin/test_edit.html', quiz=quiz, questions=questions)

@admin_bp.route('/tests/<int:quiz_id>/delete', methods=['POST'])
@login_required
@admin_required
def test_delete(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    for test in quiz.tests:
        for answer in test.answers:
            db.session.delete(answer)
        db.session.delete(test)
    db.session.delete(quiz)
    db.session.commit()
    flash('Тест удалён!', 'success')
    return redirect(url_for('admin.tests_list')
)