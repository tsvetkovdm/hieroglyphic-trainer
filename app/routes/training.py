import re
from flask import Blueprint, render_template, redirect, request, url_for, flash
from flask_login import login_required, current_user
from app.db import get_connection

training = Blueprint('training', __name__)

def normalize(text):
    return re.sub(r'\s+', ' ', text.strip().lower())


def is_answer_correct(user_answer, correct_meaning):
    user_answer = normalize(user_answer)
    allowed = [normalize(part) for part in re.split(r'[;,/]', correct_meaning)]
    return user_answer in allowed

@training.route('/start/', methods=['GET','POST'])
@login_required
def start_training():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute ('''
                     SELECT id, name FROM "training_mode"
                     WHERE access_level >= %s
                     ''',
                     (current_user.role_id,))
        modes = cur.fetchall()
    
    if request.method == 'POST':
        selected_mode = request.form['mode_id']
        return redirect(url_for('training.training_session', mode_id=selected_mode))

    return render_template('training/select_mode.html', modes=modes)

@training.route('/<int:mode_id>', methods=['GET', 'POST'])
@login_required
def training_session(mode_id):
    with get_connection() as conn:
        cur = conn.cursor()
        
        # Создание сессии
        cur.execute('''
                    INSERT INTO training_session (user_id, mode_id, date_started)
                    VALUES (%s, %s, CURRENT_DATE)
                    RETURNING id
                    ''', (current_user.id, mode_id))
        session_id = cur.fetchone()[0]

        # Выбор 10 случайных иероглифов 
        cur.execute('''
                    SELECT id FROM learning_object
                    ORDER BY random() LIMIT 10
                    ''')
        object_ids = [row[0] for row in cur.fetchall()]

        # Добавление предметов в training_item
        for object_id in object_ids:
            cur.execute('''
                        INSERT INTO training_item (session_id, object_id)
                        VALUES (%s, %s)
                        ''', (session_id, object_id))
        conn.commit()

    return redirect(url_for('training.training_question', session_id=session_id, index=0))

@training.route('/<int:session_id>/question/<int:index>', methods=['GET', 'POST'])
@login_required
def training_question(session_id, index):
    with get_connection() as conn:
        cur = conn.cursor()
        
        # Получить training_items по порядку
        cur.execute('''
                    SELECT ti.id, lo.symbol, lo.meaning, lo.pinyin
                    FROM training_item ti
                    JOIN learning_object lo ON ti.object_id = lo.id
                    WHERE ti.session_id = %s
                    ORDER BY ti.id
                    ''', (session_id,))
        items = cur.fetchall()

        # Получаем режим тренировки
        cur.execute('SELECT mode_id FROM training_session WHERE id = %s', (session_id,))
        mode_id = cur.fetchone()[0]

    if index >= len(items):
        return redirect(url_for('training.training_result', session_id=session_id))

    item_id, symbol, meaning, pinyin = items[index]

    # Настраиваем вопрос в зависимости от режима
    if mode_id == 1:
        prompt = symbol
        expected_answer = meaning
        label = "Введите значение:"
    elif mode_id == 2:
        prompt = pinyin
        expected_answer = symbol
        label = "Введите иероглиф:"
    elif mode_id == 3:
        prompt = meaning
        expected_answer = symbol
        label = "Введите иероглиф:"
    else:
        prompt = symbol
        expected_answer = meaning
        label = "Введите значение:"

    if request.method == 'POST':
        answer = request.form['answer'].strip().lower()
        expected = expected_answer.strip().lower()
        is_correct = is_answer_correct(answer, expected_answer)

        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
                        UPDATE training_item
                        SET is_correct = %s, user_answer = %s
                        WHERE id = %s
                        ''', (is_correct, answer, item_id))
            conn.commit()

        flash(f"{'✅ Правильно!' if is_correct else f'❌ Неверно. Правильно: ' + expected}")
        return redirect(url_for('training.training_question', session_id=session_id, index=index + 1))

    return render_template('training/question.html', symbol=prompt, mode_id=mode_id, index=index + 1, total=len(items), label=label)

@training.route('/<int:session_id>/result')
@login_required
def training_result(session_id):
    with get_connection() as conn:
        cur = conn.cursor()

        # Получить все ответы пользователя по тренировке
        cur.execute('''
                    SELECT ts.mode_id, lo.symbol, lo.meaning, lo.pinyin,
                        ti.user_answer, ti.is_correct
                    FROM training_item ti
                    JOIN learning_object lo ON ti.object_id = lo.id
                    JOIN training_session ts ON ti.session_id = ts.id
                    WHERE ti.session_id = %s
                    ORDER BY ti.id
                    ''', (session_id,))
        rows = cur.fetchall()

        # Определим количество правильных ответов
        correct_count = sum(1 for row in rows if row[5])
        total = len(rows)
        correct_percent = round((correct_count / total) * 100, 2)
        result_string = f"{correct_count} из {total} ({correct_percent} %)"

        # Обновим таблицу training_session с результатом и датой окончания
        cur.execute('''
                    UPDATE training_session
                    SET date_ended = CURRENT_TIMESTAMP, result = %s
                    WHERE id = %s
                    ''', (result_string, session_id))
        conn.commit()

    return render_template('training/result.html', results=rows, result_string=result_string)

@training.route('/history')
@login_required
def history():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
                    SELECT ts.id, ts.date_started, ts.date_ended, tm.name, ts.result
                    FROM training_session ts
                    JOIN training_mode tm ON ts.mode_id = tm.id
                    WHERE ts.user_id = %s
                    ORDER BY ts.date_started DESC
                    ''', (current_user.id,))
        sessions = cur.fetchall()

    return render_template('training/history.html', sessions=sessions)
