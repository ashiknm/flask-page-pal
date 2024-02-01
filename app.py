from flask import Flask, render_template, url_for ,g, redirect, request, jsonify
from database import get_database, connect_to_database
import requests 
from dotenv import load_dotenv
import os
import nltk
from nltk.corpus import stopwords
from nltk.cluster.util import cosine_distance
import numpy as np





app = Flask(__name__, static_url_path='/static', static_folder='static')

app.config['TEMPLATES_AUTO_RELOAD'] = True

api_key = os.getenv('API_KEY')

@app.teardown_appcontext
def close_database(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/')
def homePage():
    return render_template('homePage.html')

@app.route('/get_top_books', methods=['GET', 'POST'])
def get_top_books():
    if request.method == 'POST':
        book_title = request.form.get('title')

        # Call the Google Books API with your API key and book title
        url = 'https://www.googleapis.com/books/v1/volumes?q=intitle:{}&maxResults=10&key={}'.format(book_title, api_key)


        response = requests.get(url)
        data = response.json()

        # Extract and return the top 10 books
        top_books = data.get('items', [])
    else:
        top_books = []  # Default to an empty list when there's no search query

    return render_template('homePage.html', top_books=top_books)
    



@app.route('/booklist')
def booklist():
    db = get_database()
    cursor = db.execute('''
            SELECT DISTINCT b.book_id, b.book_title, b.book_language, b.publisher, b.page_count, 
                            b.book_description, b.thumbnail, GROUP_CONCAT(a.author_name) AS authors
            FROM books AS b
            LEFT JOIN authors AS a ON b.book_id = a.book_id
            GROUP BY b.book_id
        ''')
        
        # Fetch all the rows as dictionaries
    books = []
    for row in cursor.fetchall():
        book_entry = dict(row)
        authors = book_entry.get('authors')
        if authors:
            book_entry['authors'] = authors.split(',')
        else:
            book_entry['authors'] = []
        books.append(book_entry)
    
        # Close the database connection
    db.close()
        
        # Return the book list with authors as JSON
    return render_template('bookList.html', books=books)


def get_book_info(book_id):
    url = f'https://www.googleapis.com/books/v1/volumes/{book_id}?key={api_key}'

    response = requests.get(url)
    return  response.json()

    


@app.route('/singlebook/<id>/<title>')
def singlebook(id, title):
    book_info = get_book_info(id)
    return render_template('singleBook.html', book_info=book_info)

def sentence_similarity(sent1, sent2, stopwords=None):
    if stopwords is None:
        stopwords = []
    sent1 = [word.lower() for word in sent1]
    sent2 = [word.lower() for word in sent2]
    all_words = list(set(sent1 + sent2))
    vector1 = [0] * len(all_words)
    vector2 = [0] * len(all_words)
    for w in sent1:
        if w not in stopwords:
            vector1[all_words.index(w)] += 1
    for w in sent2:
        if w not in stopwords:
            vector2[all_words.index(w)] += 1
    return 1 - cosine_distance(vector1, vector2)

def generate_summary(text, top_n=5):
    sentences = nltk.sent_tokenize(text)
    stop_words = set(stopwords.words('english'))
    sentence_scores = []
    for i in range(len(sentences)):
        for j in range(len(sentences)):
            if i == j:
                continue
            similarity = sentence_similarity(sentences[i], sentences[j], stop_words)
            sentence_scores.append((i, j, similarity))
    sentence_scores.sort(key=lambda x: x[2], reverse=True)
    summary_sentences = []
    selected_sentences = []
    for i, j, score in sentence_scores:
        if sentences[i] not in selected_sentences and sentences[j] not in selected_sentences:
            summary_sentences.append(sentences[i])
            selected_sentences.append(sentences[i])
            if len(summary_sentences) >= top_n:
                break
    return ' '.join(summary_sentences)


@app.route('/summarize_text/<id>/<description>', )
def summarize_text(id, description):
    book_info = get_book_info(id)
    summary = generate_summary(description)

    return render_template('summeryPage.html', summary=summary, book_info=book_info)

@app.route('/savebook', methods = ["POST", "GET"])
def savebook():
    db = get_database()

    data = request.get_json()

    book_id = data.get('bookId')
    book_title = data.get('title')
    book_language = data.get('language')
    publisher = data.get('publisher')
    page_count = data.get('pageCount')
    book_description = data.get('description')
    thumbnail = data.get('thumbnail')


    authors = data.get('authors')

    availaible_book = db.execute('select * from books where book_id = ?',[book_id])
    book_available = availaible_book.fetchone()

    if book_available:
        return jsonify("book saved succesfully ")
        
    else:
        db.execute('insert into books(book_id, book_title, book_language, publisher,page_count, book_description, thumbnail ) values ( ?, ?, ?, ?, ?, ?, ?)',[book_id, book_title, book_language , publisher, page_count,book_description, thumbnail ])

        if authors:
            for author_name in authors:
                db.execute('INSERT INTO authors (author_name, book_id) VALUES (?, ?)', [author_name, book_id])

        db.commit()

    # return redirect(url_for('singlebook', id=id, title=title))
    return redirect(url_for('homePage'))

@app.route('/deletebook/<id>')
def deletebook(id):
    try:
        # Connect to the database
        db = connect_to_database()
        
        # Check if the book with the given book_id exists
        cursor = db.execute('SELECT * FROM books WHERE book_id = ?', [id])
        book = cursor.fetchone()
        
        if not book:
            db.close()
            return jsonify({'error': 'Book not found'}), 404

        # Delete the book by its book_id
        db.execute('DELETE FROM books WHERE book_id = ?', [id])
        db.execute('DELETE FROM authors WHERE book_id = ?', [id])

        # Commit the changes and close the database connection
        db.commit()
        db.close()

        return redirect(url_for('booklist'))
    

    except Exception as e:
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    app.run(debug = True)
