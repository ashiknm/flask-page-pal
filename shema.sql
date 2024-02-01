create table if not exists books ( 
    book_id text,
    book_title text,
    book_language text,
    publisher text,
    page_count text,
    book_description text,
    thumbnail text
) ;

CREATE TABLE IF NOT EXISTS authors (
    author_id integer primary key AUTOINCREMENT,
    author_name text,
    book_id INTEGER NOT NULL,
    FOREIGN KEY (book_id) REFERENCES books (book_id)
);