from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Result, Exam, Quiz, Test
from datetime import datetime

student_bp = Blueprint('student', __name__)

# Экзамены и тесты: фильтрация по предмету и классу
@student_bp.route('/exams', methods=['GET'])
@login_required
def exams():
    subject = request.args.get('subject') or None
    grade = request.args.get('grade') or None
    search_query = request.args.get('q', '').strip()

    subjects = [row[0] for row in db.session.query(Exam.title).distinct()]
    grades = [row[0] for row in db.session.query(Exam.grade).distinct()]

    exams_query = Exam.query
    if subject:
        exams_query = exams_query.filter(Exam.title == subject)
    if grade:
        exams_query = exams_query.filter(Exam.grade == grade)
    if search_query:
        exams_query = exams_query.filter(
            Exam.title.ilike(f"%{search_query}%") | Exam.description.ilike(f"%{search_query}%")
        )
    exams = exams_query.all()

    # Тесты (Quiz)
    quizzes_query = Quiz.query
    if subject:
        quizzes_query = quizzes_query.filter(Quiz.title == subject)
    if grade:
        quizzes_query = quizzes_query.filter(Quiz.description.ilike(f"%{grade}%") if Quiz.description is not None else False)
    if search_query:
        quizzes_query = quizzes_query.filter(
            Quiz.title.ilike(f"%{search_query}%") | Quiz.description.ilike(f"%{search_query}%")
        )
    quizzes = quizzes_query.all()

    return render_template(
        'student/exams.html',
        exams=exams,
        quizzes=quizzes,
        subjects=subjects,
        grades=grades,
        selected_subject=subject,
        selected_grade=grade
    )

# Старт экзамена
@student_bp.route('/exam/start/<int:exam_id>', methods=['GET'])
@login_required
def exam_start(exam_id):
    exam = Exam.query.get(exam_id)
    if not exam:
        flash("Экзамен не найден.", "danger")
        return redirect(url_for('student.exams'))
    session["exam_progress"] = {"exam_id": exam_id, "current": 0, "answers": []}
    return redirect(url_for('student.exam_take', exam_id=exam_id))

# Прохождение экзамена
@student_bp.route('/exam/take/<int:exam_id>', methods=['GET', 'POST'])
@login_required
def exam_take(exam_id):
    exam = Exam.query.get(exam_id)
    if not exam:
        flash("Экзамен не найден.", "danger")
        return redirect(url_for('student.exams'))
    questions = exam.tests
    progress = session.get("exam_progress")
    if not progress or progress.get("exam_id") != exam_id:
        return redirect(url_for('student.exam_start', exam_id=exam_id))
    current = progress["current"]
    if request.method == "POST":
        answer = request.form.get("answer")
        progress["answers"].append(int(answer) if answer is not None else -1)
        progress["current"] += 1
        session["exam_progress"] = progress
        if progress["current"] >= len(questions):
            return redirect(url_for('student.exam_result', exam_id=exam_id))
        return redirect(url_for('student.exam_take', exam_id=exam_id))
    question = questions[current]
    answers = sorted(question.answers, key=lambda a: a.id)
    return render_template(
        'student/take_exam.html',
        exam=exam,
        question=question,
        answers=answers,
        current=current + 1,
        total=len(questions)
    )

# Результат экзамена
@student_bp.route('/exam/result/<int:exam_id>', methods=['GET'])
@login_required
def exam_result(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    questions = exam.tests
    progress = session.pop("exam_progress", None)
    if not progress or progress.get("exam_id") != exam_id:
        flash("Ошибка прохождения экзамена.", "danger")
        return redirect(url_for('student.exams'))
    user_answers = progress["answers"]
    correct_answers = [
        next((i for i, a in enumerate(sorted(q.answers, key=lambda a: a.id)) if a.is_correct), None)
        for q in questions
    ]
    score = sum(1 for u, c in zip(user_answers, correct_answers) if u == c)
    percent = int(score / len(correct_answers) * 100) if correct_answers else 0

    result = Result(
        user_id=current_user.id,
        item_id=exam_id,
        item_type='exam',
        title=exam.title,
        date=datetime.utcnow(),
        score=percent
    )
    db.session.add(result)
    db.session.commit()

    return render_template(
        'student/exam_results.html',
        exam=exam,
        score=score,
        percent=percent,
        total=len(correct_answers)
    )

# --- Тесты (Quiz) ---

# Старт теста
@student_bp.route('/test/start/<int:quiz_id>', methods=['GET'])
@login_required
def test_start(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        flash("Тест не найден.", "danger")
        return redirect(url_for('student.exams'))
    session["test_progress"] = {"quiz_id": quiz_id, "current": 0, "answers": []}
    return redirect(url_for('student.test_take', quiz_id=quiz_id))

# Прохождение теста
@student_bp.route('/test/take/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def test_take(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        flash("Тест не найден.", "danger")
        return redirect(url_for('student.exams'))
    questions = quiz.tests
    progress = session.get("test_progress")
    if not progress or progress.get("quiz_id") != quiz_id:
        return redirect(url_for('student.test_start', quiz_id=quiz_id))
    current = progress["current"]
    if request.method == "POST":
        answer = request.form.get("answer")
        progress["answers"].append(int(answer) if answer is not None else -1)
        progress["current"] += 1
        session["test_progress"] = progress
        if progress["current"] >= len(questions):
            return redirect(url_for('student.test_result', quiz_id=quiz_id))
        return redirect(url_for('student.test_take', quiz_id=quiz_id))
    question = questions[current]
    answers = sorted(question.answers, key=lambda a: a.id)
    return render_template(
        'student/take_test.html',
        quiz=quiz,
        question=question,
        answers=answers,
        current=current + 1,
        total=len(questions)
    )

# Результат теста
@student_bp.route('/test/result/<int:quiz_id>', methods=['GET'])
@login_required
def test_result(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = quiz.tests
    progress = session.pop("test_progress", None)
    if not progress or progress.get("quiz_id") != quiz_id:
        flash("Ошибка прохождения теста.", "danger")
        return redirect(url_for('student.exams'))
    user_answers = progress["answers"]
    correct_answers = [
        next((i for i, a in enumerate(sorted(q.answers, key=lambda a: a.id)) if a.is_correct), None)
        for q in questions
    ]
    score = sum(1 for u, c in zip(user_answers, correct_answers) if u == c)
    percent = int(score / len(correct_answers) * 100) if correct_answers else 0

    result = Result(
        user_id=current_user.id,
        item_id=quiz_id,
        item_type='quiz',
        title=quiz.title,
        date=datetime.utcnow(),
        score=percent
    )
    db.session.add(result)
    db.session.commit()

    return render_template(
        'student/test_results.html',
        quiz=quiz,
        score=score,
        percent=percent,
        total=len(correct_answers)
    )

# Профиль
@student_bp.route('/profile')
@login_required
def profile():
    stats = {
        "total_exams": 0,
        "total_tests": 0,
        "avg_exam_score": 0,
        "avg_test_score": 0,
    }
    passed_exams = []
    passed_tests = []
    results = current_user.results
    if results:
        exams = [r for r in results if r.item_type == 'exam']
        tests = [r for r in results if r.item_type == 'quiz']
        stats["total_exams"] = len(exams)
        stats["total_tests"] = len(tests)
        stats["avg_exam_score"] = round(sum(r.score for r in exams) / len(exams), 1) if exams else 0
        stats["avg_test_score"] = round(sum(r.score for r in tests) / len(tests), 1) if tests else 0
        passed_exams = exams
        passed_tests = tests

    return render_template(
        'student/profile.html',
        stats=stats,
        passed_exams=passed_exams,
        passed_tests=passed_tests
    )