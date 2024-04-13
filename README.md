# DIY-Ultimate-AI-Powered-Autoblog-Using-RSS
DIY: Ultimate AI Powered Autoblog Using RSS (Python, Ollama, Beautiful Soup, Feedparser, SQLite)

This project shows you how to use RSS Feeds to scrape websites, and then rewrite the posts on those websites using Ollama and an LLM.

process-autoblog.py -- runs a constant loop to check for new posts, rewrite them and store them to the database.

webpage-autoblog.py -- creates a web page by selecting all of the posts from the database and then printing them out in HTML.

feeds.txt - add feeds into this file on separate lines so that they are processed.

## Warning
Make sure Ollama is running on your system before you run your Python script

There may be copyright legal issues if you use this on a public site.

Running Ollama constantly can be hard on your computer.


## YouTube Video

https://youtu.be/u3U6NIZ-wGc


## Requirements
Install Ollama - https://ollama.com, make sure you pull the correct model using `ollama run llama2:14b`

pip3 install ollama

pip3 install bottle

pip3 install BeautifulSoup4

pip3 install feedparser

sqlite - install from https://www.sqlite.org/download.html

