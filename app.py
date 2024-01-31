from flask import Flask, render_template, url_for ,g, redirect, request, jsonify
import requests 
from dotenv import load_dotenv
import os

app = Flask(__name__)

@app.route('/')
def homePage():
    return render_template('homePage.html')

@app.route('/get_top_books', methods=['GET', 'POST'])
def get_top_books():
    if request.method == 'POST':
        book_title = request.form.get('title')


        # Get the API key from the environment variables
        api_key = os.getenv('API_KEY')

        # Call the Google Books API with your API key and book title
        url = f'https://www.googleapis.com/books/v1/volumes?q=intitle:{book_title}&maxResults=10&key={api_key}'

        response = requests.get(url)
        data = response.json()

        # Extract and return the top 10 books
        top_books = data.get('items', [])
    else:
        top_books = []  # Default to an empty list when there's no search query

    return render_template('homePage.html', top_books=top_books)
    

@app.route('/booklist')
def booklist():
    return render_template('bookList.html')

@app.route('/singlebook/<id>/<title>')
def singlebook(id, title):
    api_key = os.getenv('API_KEY')

    # Call the Google Books API with your API key and book title
    url = f'https://www.googleapis.com/books/v1/volumes/{id}?key={api_key}'

    response = requests.get(url)
    book_info = response.json()



    return render_template('singleBook.html', book_info=book_info)


if __name__ == '__main__':
    app.run(debug = True)