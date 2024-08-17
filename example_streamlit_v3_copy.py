import streamlit as st
import sqlite3
from openai import OpenAI
import requests
from requests.auth import HTTPProxyAuth
import httpx
import hashlib
import math
import re

def setup_database():
    conn = sqlite3.connect('admin_panel.sqlite')
    c = conn.cursor()
    
    # Create a users table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()


def register_user(username, password):
    conn = sqlite3.connect('admin_panel.sqlite')
    c = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        st.error("Username already exists")
    conn.close()

def validate_user(username, password):
    conn = sqlite3.connect('admin_panel.sqlite')
    c = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    c.execute('SELECT user_id FROM users WHERE username=? AND password=?', (username, hashed_password))
    user = c.fetchone()
    conn.close()
    return user

def st_write_large_text(text):
    st.markdown(f'<div style="font-size: 36px;">{text}</div>', unsafe_allow_html=True)

# Example usage
def get_summary(book_id, chapter_id):
    conn = sqlite3.connect('summary_questions1_v2.sqlite')
    c = conn.cursor()
    c.execute('SELECT chapter_summary FROM summary_questions WHERE id_chapter=? and name_book=?', (chapter_id, book_id))
    summary = c.fetchone()
    conn.close()
    return summary[0] if summary else "Краткое содержание не найдено"

def get_questions(book_id, chapter_id):
    conn = sqlite3.connect('summary_questions1_v2.sqlite')
    c = conn.cursor()
    c.execute('SELECT questions_summary FROM summary_questions WHERE id_chapter=? and name_book=?', (chapter_id, book_id))
    summary = c.fetchone()
    conn.close()
    return summary[0] if summary else "Краткое содержание не найдено"

def add_content(book_id, id_chapter, user_content, id_question):
    conn = sqlite3.connect('book_contents.db')
    c = conn.cursor()
    c.execute('''
    INSERT INTO book_contents (name_book, id_chapter, user_content, question_id)
    VALUES (?, ?, ?, ?)
    ''', (book_id, id_chapter, user_content, id_question))
    conn.commit()
    conn.close()

def add_summary_length_info(books):
    # Проходим по всем книгам и главах, чтобы добавить информацию о длине краткого содержания
    for book_id, book in books.items():
        total_length = 0
        for chapter_id in book['chapters']:
            summary = get_summary(book_id, chapter_id)
            total_length += len(summary)
        # Добавляем информацию о длине краткого содержания в описание книги
        books[book_id]['summary_length'] = total_length
        books[book_id]['image_path'] = book.get('image_path') 
    return books

def update_answers_user(book_id, chapter_id, user_id, text_user, text_gpt, id_question):
    conn = sqlite3.connect('summary_questions1_v2.sqlite')
    c = conn.cursor()
    user_column = f'answers_user{id_question}'
    gpt_column = f'answers_gpt{id_question}'
    c.execute(f'''
        UPDATE summary_questions
        SET {user_column} = ?, {gpt_column} = ?, user_id = ?
        WHERE name_book = ? AND id_chapter = ?
    ''', (text_user,text_gpt, user_id,  book_id, chapter_id))
    conn.commit()
    conn.close()

def get_user_answers(book_id, chapter_id, user_id, id_question):
    conn = sqlite3.connect('summary_questions1_v2.sqlite')
    c = conn.cursor()
    user_column = f'answers_user{id_question}'
    gpt_column = f'answers_gpt{id_question}'
    c.execute(f'''
        SELECT {user_column}, {gpt_column} FROM summary_questions
        WHERE name_book = ? AND id_chapter = ? AND user_id = ?
    ''', (book_id, chapter_id, user_id))
    answers = c.fetchone()
    conn.close()
    if answers == None:
        return (None, None)
    return answers





books = {
    "7 навыков высокоэффективных людей": {
        "title": "7 навыков высокоэффективных людей",
        "author": "Стивен Кови",
        "image_path": 'kovi1.jpg',
        "chapters": {
            1: "Глава 1",
            2: "Глава 2",
            3: "Глава 3",
            4: "Глава 4",
            5: "Глава 5",
        }
    },
    "Психология человека от рождения до смерти": {
        "title": "Психология человека от рождения до смерти",
        "image_path": 'reana1.jpg',
        "author": "Реана A.A. ",
        "chapters": {
            1: "Глава 1 История исследований развития",
            2: "Глава 2 Формы и области (сферы) развития",
            3: "Глава 3 Цели развития",
            4: "Глава 4 Цели психического развития. итоги",
            5: "Глава 5 Понятие факторов психического развития",
        }
    }, 
    "Открывая организации будущего": {
        "title": "Открывая организации будущего",
        "image_path": "lalu.png",
        "author": "Фредерик Лалу",
        "chapters": {
            1: "Глава 1.1 Смена парадигмы: прошлое и настоящее организационной модели",
            2: "Глава 1.2 О стадиях развития",
            3: "Глава 1.3 Эволюционная Бирюзовая стадия",
            4: "Глава 2.1 Три открытия и одна метафора",
            5: "Глава 2.2 Самоуправление (организационные структуры)",
            6: "Глава 2.3 Самоуправление (процессы)",
            7: "Глава 2.4 Стремление к целостности (Общая практика)",
            8: "Глава 2.5 Стремление к целостности (HR-процессы)",
            9: "Глава 2.6 Внимание к эволюционной цели организации",
            10: "Глава 2.7 Общие культурные черты",
            11: "Глава 3.1 Необходимые условия",
        }
    }, 
    "Моя Борьба": {
        "title": "Моя Борьба",
        "image_path": "adolf.jpg",
        "author": "Адольф Гитлер",
        "chapters": {
            1: "Глава 1. В ОТЧЕМ ДОМЕ",
            2: "Глава 2. ВЕНСКИЕ ГОДЫ УЧЕНИЯ И МУЧЕНИЯ",
            3: "Глава 3. ОБЩЕПОЛИТИЧЕСКИЕ РАЗМЫШЛЕНИЯ, СВЯЗАННЫЕ С МОИМ ВЕНСКИМ ПЕРИОДОМ",
            4: "Глава 4. МЮНХЕН",
            5: "Глава 5. МИРОВАЯ ВОЙНА",
        }
    }

}

setup_database()
st.title("Админская панель")

# User registration
if 'user_id' not in st.session_state:
    st.sidebar.header("Регистрация")
    username = st.sidebar.text_input("Ник")
    password = st.sidebar.text_input("Пароль", type="password")
    if st.sidebar.button("Регистрация"):
        register_user(username, password)
        st.sidebar.success("Пользователь успешно зарегистрирован. Пожалуйста войдите")

# User login
if 'user_id' not in st.session_state:
    st.sidebar.header("Вход")
    username = st.sidebar.text_input("Ник", key="login_username")
    password = st.sidebar.text_input("Пароль", type="password", key="login_password")
    if st.sidebar.button("Вход"):
        user = validate_user(username, password)
        if user:
            st.session_state.user_id = user[0]
            st.sidebar.success("Успешно вошли")
            #st.experimental_rerun()
            st.rerun()
        else:
            st.sidebar.error("Неправильные данные")

if 'user_id' in st.session_state:
    st.write(f"Вошли как user ID: {st.session_state.user_id}")
    if st.sidebar.button("Logout"):
        logout()


if 'book_selected' not in st.session_state:
    st.session_state.book_selected = False

if 'chapter_selected' not in st.session_state:
    st.session_state.chapter_selected = False


books = add_summary_length_info(books)
average_num_words_minute = 863

if not st.session_state.book_selected:
    st.write("Выберите книгу:")
    for book_id, book in books.items():
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(book['image_path'], width=100)
        with col2:
            if st.button(f"{books[book_id]['title']}"):
                st.session_state.book_selected = True
                st.session_state.selected_book_id = book_id
                #st.experimental_rerun()
                st.rerun()
            st.write(f"Время чтения книги ~ {math.ceil(books[book_id]['summary_length']/average_num_words_minute)} мин. ")
            st.write(f"Автор: {book['author']}")

else:
    book_id = st.session_state.selected_book_id
    user_id = st.session_state.user_id
    st_write_large_text(f"Вы выбрали {books[book_id]['title']}")
    
    if not st.session_state.chapter_selected:
        st.write("Выберите главу:")
        for chapter_id, chapter_title in books[book_id]['chapters'].items():
            if st.button(chapter_title):
                st.session_state.chapter_selected = True
                st.session_state.selected_chapter_id = chapter_id
                #st.experimental_rerun()
                st.rerun()
        if st.button('Вернуться к выбору книг'):
            st.session_state.book_selected = False
            st.session_state.chapter_selected = False
            #st.experimental_rerun()
            st.rerun()
    else:
        chapter_id = st.session_state.selected_chapter_id
        book_id = st.session_state.selected_book_id
        summary = get_summary(book_id, chapter_id)
        st.write(summary)
        st_write_large_text("Вам предлагается ответить на вопросы по краткому содержанию.")
        questions = get_questions(book_id, chapter_id)
        questions = re.split(r'(?=\d+\.\s)', questions)
        questions = questions[1:][:5]
        question_index = 0
        print("глава и название книги: ", chapter_id, book_id)




        if "question_index" not in st.session_state:
            st.session_state.question_index = 0


        def next_question():
            if st.session_state.question_index  < len(questions)-1:
                st.session_state.question_index += 1
                #st.experimental_rerun()
                st.rerun()
            else:
                st.write("Вы ответили на все вопросы")



        current_question = questions[st.session_state.question_index]
        st.write(current_question)

        # Check and display previous answers
        previous_answers = get_user_answers(book_id, chapter_id, user_id, st.session_state.question_index )
        print(book_id, chapter_id, user_id, st.session_state.question_index)
        print(previous_answers)
        if previous_answers != (None, None):
            st_write_large_text("Вы уже отвечали на эти вопросы.")
            st.write(f"Ваш предыдущий ответ: {previous_answers[0]}")
            st.write(f"Ответ GPT: {previous_answers[1]}")

            st_write_large_text("Если вы хотите еще раз ответить, напишите ответ ниже")
            user_input = st.text_area("Напишите ваш текст ниже:")
            if st.button('Сохранить текст'):
	            print("1111111")
	            # add_content(book_id, chapter_id, user_input, st.session_state.question_index )
	            # print("22222222")
	            st.success("Ваш текст был сохранен!")
	            prompt_example = f'''Ты помогаешь оценить насколько правильный ответ по тексту. Есть текст: {summary}. На вопрос: {questions} был получен ответ: {user_input}. Оцени ответ и дай свою обратную связь'''
	            api_key='sk-H1d1x8cV1k0UHZJzRkCzdTYSXbPjMqJ0'
	            client = OpenAI(api_key=api_key, base_url="https://api.proxyapi.ru/openai/v1")

	            response = client.chat.completions.create(
	                model="gpt-4o-mini", # Или gpt-4,
	                # в данной задаче грейдер не проверяет какую модель вы выбрали,
	                # но советуем попробовать gpt-4 в качестве экперимента.
	                messages=[{
	                        "role": "user",
	                        "content": prompt_example,}
	                ],
	                temperature=0.7  # Уровень случайности вывода модели
	                )
	            st.write(response.choices[0].message.content)
	            update_answers_user(book_id, chapter_id,user_id, user_input, response.choices[0].message.content, st.session_state.question_index)

        else:
            user_input = st.text_area("Напишите ваш текст ниже:")
            if st.button('Сохранить текст'):
                #add_content(book_id, chapter_id, user_input, st.session_state.question_index )
                #st.success("Ваш текст был сохранен!")
                prompt_example = f'''Ты помогаешь оценить насколько правильный ответ по тексту. Есть текст: {summary}. На вопрос: {questions} был получен ответ: {user_input}. Оцени ответ и дай свою обратную связь'''
                api_key='sk-H1d1x8cV1k0UHZJzRkCzdTYSXbPjMqJ0'
                client = OpenAI(api_key=api_key, base_url="https://api.proxyapi.ru/openai/v1")

                response = client.chat.completions.create(
                    model="gpt-4o-mini", # Или gpt-4,
                    # в данной задаче грейдер не проверяет какую модель вы выбрали,
                    # но советуем попробовать gpt-4 в качестве экперимента.
                    messages=[
                        {
                            "role": "user",
                            "content": prompt_example,
                        }
                    ],
                    temperature=0.7  # Уровень случайности вывода модели
                )
                st.write(response.choices[0].message.content)
                update_answers_user(book_id, chapter_id,user_id, user_input, response.choices[0].message.content, st.session_state.question_index)

        if st.button("Следующий вопрос"):
            print("current_index = ", st.session_state.question_index)
            next_question()


        if st.button('Вернуться к выбору глав'):
            st.session_state.chapter_selected = False
            st.session_state.question_index  = 0
            #st.experimental_rerun()
            st.rerun()

        if st.button('Перейти к следующей главе'):
            st.session_state.chapter_selected = True
            st.session_state.selected_chapter_id += 1
            st.session_state.question_index  = 0
            #st.experimental_rerun()
            st.rerun()

    # else:
    #     st_write_large_text("Вы ответили на все вопросы в этой главе.")
    #     if st.button('Вернуться к выбору глав'):
    #         st.session_state.chapter_selected = False
    #         st.session_state.question_index = 0
    #         st.experimental_rerun()

    # if st.button('Перейти к следующей главе'):
    #     st.session_state.chapter_selected = True
    #     st.session_state.selected_chapter_id += 1
    #     st.session_state.question_index = 0
    #     st.experimental_rerun()


# TODO разобраться с логикой обработки вложенности, как лучше вопросы делать?




