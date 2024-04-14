#Script to Process RSS Feeds and rewrite posts with AI
#Results are added to SQLite database
#Use webpage-autoblog.py to view new posts as a web page
import sqlite3
import os
import ollama
import aiohttp
from bs4 import BeautifulSoup
import feedparser
import datetime
import asyncio
import aiofiles
from functools import partial

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
async def parse(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()  # This will raise an exception if there's an error.
            text = await response.text()

    soup = BeautifulSoup(text, 'html.parser')

    p_tags = soup.find_all('p')
    title = soup.find('title')

    page_title = title.text
    page_text=''
    for p in p_tags:
        page_text = f'{page_text} {p.text}'

    return page_title,page_text

#LLM Function - Write the title
async def write_title(post_title):
    query = f'''rewrite this title for a blog post\
            -- give only one response \
            -- do not say anything such as  -- Heres a possible rewrite of the title for a blog post:\
            -- {post_title}'''
    loop = asyncio.get_event_loop()
    chat_func = partial(ollama.chat, model='llama2:13b', messages=[
    {
        'role': 'user',
        'content': query,
    },
    ])
    response = await loop.run_in_executor(None, chat_func)
    return response['message']['content']

#LLM Function - Write the post
async def write_post(post_text):
    query = f'Write a new blog post of a minimum 500 words based on this information \
            -- do not add a title \
            -- do not say anything such as "this article" \
            -- {post_text}'
    loop = asyncio.get_event_loop()
    chat_func = partial(ollama.chat, model='llama2:13b', messages=[
    {
        'role': 'user',
        'content': query,
    },
    ])
    response = await loop.run_in_executor(None, chat_func)
    return response['message']['content']

async def process_feed(feed, lock):
    print(f'FEED -->> {feed}')

    loop = asyncio.get_event_loop()
    feed_output = await loop.run_in_executor(None, feedparser.parse,feed)

    for item in feed_output.entries:
        link = item['link']
        if database.db_check_record(link) == None:
            async with lock:
                try:
                    response = await parse(link)
                    title = response[0]
                    post_original = response[1]
                    title = await write_title(title)

                    # Clean up the Title returned from LLM.  This works for llama2
                    title = title.split(':')
                    title = title[1]
                    title = title.replace('"','')
                    print(f'TITLE --- {title}')

                    # Wrap Post Paragagraphs in <p> tags
                    post=''
                    post_raw = await write_post(post_original)
                    post_list = post_raw.split('\n')
                    for item in post_list:
                        post = f'{post} <p>{item}</p>'
                    print(f'POST ---- {post}')
                    return database.db_insert(link,post_original,title, post)
                except Exception as e:
                    print(f'Error processing feed {feed}: {e}') 
        else:
            print('This blog has already been processed.')
            
async def collect_process():
    # Open the file in read mode and read lines
    async with aiofiles.open('feeds.txt', 'r') as feedurl:
        feed_list = [line.strip() for line in await feedurl.readlines()]
    lock = asyncio.Lock()
    tasks = [process_feed(feed, lock) for feed in feed_list]
    await asyncio.gather(*tasks)

#Create database table if it does not exist
database.db_create()

async def Main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        try:
            await collect_process()
            await asyncio.sleep(1)
        finally:
            loop.close()

# Run the main function
asyncio.run(Main())