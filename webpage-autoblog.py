#This is a web app that creates a web page from the
#results that are stored in a SQLite database
#Run process-autoblog.py to scrape RSS feeds and create posts
from bottle import route, run
import sqlite3
import os

#Class For Interacting with Database
#path() is used for using database in same folder as script
class database:
    def path():
        current_directory = os.path.dirname(os.path.abspath(__file__))
        db_name = 'autoblog.db'
        file_path = os.path.join(current_directory, db_name)

        return file_path

    def db_select():
        file_path = database.path()
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        sql = 'select * from entry order by id desc'
        cursor.execute(sql)
        record = cursor.fetchall()
        conn.commit()
        conn.close()

        return record

#Index Page. Query form sends values back to this page
@route('/')
def index():

    #Add data to database
    record_set = database.db_select()
    
    #Create feed of previous posts
    page=''
    for record in record_set:
        page =  f'''
                    {page} 
                    <h1>{record[4]}</h1>
                    {record[5]}
                    <hr>
                '''

    return page

#Run web server.  If post 80 does not work try 8080
run(host='0.0.0.0', port=80, debug=True)