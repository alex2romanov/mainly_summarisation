import streamlit as st
import sqlite3


def get_summary(book_id, chapter_id):
    # Здесь ваша логика для получения краткого содержания
    return f"Краткое содержание для {books[book_id]['title']}, {books[book_id]['chapters'][chapter_id]}"

def get_questions(book_id, chapter_id):
    # Здесь ваша логика для получения вопросов
    return f"Вопросы для {books[book_id]['title']}, {books[book_id]['chapters'][chapter_id]}"

def add_content(book_id, chapter_id, content):
    # Здесь ваша логика для сохранения текста
    pass



books = {
    "Book1": {
        "title": "Книга 1",
        "chapters": {
            1: "Глава 1: История исследований развития",
            2: "Глава 2: Примеры и случаи",
        }
    },
    "Book2": {
        "title": "Книга 2",
        "chapters": {
            1: "Глава 1: Основы теории",
            2: "Глава 2: Практическое применение",
        }
    }
}

if 'book_selected' not in st.session_state:
    st.session_state.book_selected = False

if 'chapter_selected' not in st.session_state:
    st.session_state.chapter_selected = False

if not st.session_state.book_selected:
    st.write("Выберите книгу:")
    for book_id in books:
        if st.button(books[book_id]['title']):
            st.session_state.book_selected = True
            st.session_state.selected_book_id = book_id
            st.experimental_rerun()

else:
    book_id = st.session_state.selected_book_id
    st.write(f"Вы выбрали {books[book_id]['title']}")
    
    if not st.session_state.chapter_selected:
        st.write("Выберите главу:")
        for chapter_id, chapter_title in books[book_id]['chapters'].items():
            if st.button(chapter_title):
                st.session_state.chapter_selected = True
                st.session_state.selected_chapter_id = chapter_id
                st.experimental_rerun()
    else:
        chapter_id = st.session_state.selected_chapter_id
        summary = get_summary(book_id, chapter_id)
        st.write(summary)
        st.write("Вам предлагается ответить на вопросы по краткому содержанию.")
        questions = get_questions(book_id, chapter_id)
        st.write(questions)
        
        user_input = st.text_area("Напишите ваш текст ниже:")
        if st.button('Сохранить текст'):
            add_content(book_id, chapter_id, user_input)
            st.success("Ваш текст был сохранен!")
        
        if st.button('Вернуться к выбору глав'):
            st.session_state.chapter_selected = False
            st.experimental_rerun()
        
        if st.button('Вернуться к выбору книг'):
            st.session_state.book_selected = False
            st.session_state.chapter_selected = False
            st.experimental_rerun()


