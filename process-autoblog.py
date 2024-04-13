#Script to Process RSS Feeds and rewrite posts with AI
#Results are added to SQLite database
#Use webpage-autoblog.py to view new posts as a web page
import sqlite3
import os
import ollama
import requests
from bs4 import BeautifulSoup
import feedparser
import datetime
from time import sleep
import concurrent.futures

#Class For Interacting with Database
#path() is used for using database in same folder as script
class database:
    def path():
        current_directory = os.path.dirname(os.path.abspath(__file__))
        db_name = 'autoblog.db'
        file_path = os.path.join(current_directory, db_name)

        return file_path

    def db_create():
        file_path = database.path()
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()

        create_table = '''
                        create table if not exists entry(
                            id integer primary key,
                            time_stamp text,
                            link text,
                            post_original text,
                            title text,
                            post text
                        )
                        '''

        cursor.execute(create_table)
        conn.commit()
        conn.close()

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
    
    def db_check_record(link):
        file_path = database.path()
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        sql = f'select * from entry where link == "{link}"'
        cursor.execute(sql)
        record = cursor.fetchone()
        conn.commit()
        conn.close()

        return record

    def db_insert(link,post_original,title, post):
        time_stamp = datetime.datetime.now()
        file_path = database.path()
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        sql = 'insert into entry(time_stamp,link,post_original,title, post) values(?,?,?,?,?)'
        cursor.execute(sql,(time_stamp,link,post_original,title, post))
        conn.commit()
        conn.close()

#Scrape the Title and the Text of the post
def parse(url):
    response = requests.get(url)
    response.raise_for_status()  # This will raise an exception if there's an error.

    soup = BeautifulSoup(response.text, 'html.parser')

    p_tags = soup.find_all('p')
    title = soup.find('title')

    page_title = title.text
    page_text=''
    for p in p_tags:
        page_text = f'{page_text} {p.text}'

    return page_title,page_text 

#LLM Function - Write the title
def write_title(post_title):
    query = f'''rewrite this title for a blog post\
            -- give only one response \
            -- do not say anything such as  -- Heres a possible rewrite of the title for a blog post:\
            -- {post_title}'''
    response = ollama.chat(model='llama2:13b', messages=[
    {
        'role': 'user',
        'content': query,
    },
    ])
    response = response['message']['content']

    return response

#LLM Function - Write the post
def write_post(post_text):
    query = f'Write a new blog post of a minimum 500 words based on this information \
            -- do not add a title \
            -- do not say anything such as "this article" \
            -- {post_text}'
    response = ollama.chat(model='llama2:13b', messages=[
    {
        'role': 'user',
        'content': query,
    },
    ])
    response = response['message']['content']

    return response

def process_feed(feed):
    print(f'FEED -->> {feed}')
    feed_output = feedparser.parse(feed)

    for item in feed_output.entries:
        link = item['link']
        if database.db_check_record(link) == None:

            response = parse(link)
            title = response[0]
            post_original = response[1]
            title = write_title(title)

            #Clean up the Title returned from LLM.  This works for llama2
            title = title.split(':')
            title = title[1]
            title = title.replace('"','')
            print(f'TITLE --- {title}')

            #Wrap Post Paragagraphs in <p> tags
            post=''
            post_raw = write_post(post_original)
            post_list = post_raw.split('\n')
            for item in post_list:
                post = f'{post} <p>{item}</p>'
            print(f'POST ---- {post}')
            database.db_insert(link,post_original,title, post)
        else:
            print('record already exists')

def collect_process():
    # Open the file in read mode and read lines
    with open('feeds.txt', 'r') as f:
        feed_list = [line.strip() for line in f]

    # Use ThreadPoolExecutor to process multiple feeds concurrently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(process_feed, feed_list)

#Create database table if it does not exist
database.db_create()

while True:
    os.system('clear')
    collect_process()
    sleep(5)
