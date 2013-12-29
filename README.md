#Team Liquid Blog Ranker
This was an early scraping and analysis project I took up in my spare time in mid-2012. Team Liquid, a popular gaming site, has a blog section which they imposed a ranking mechanism on. I analysed the actual activity on blog posts to rerank based on views and comments, in order to try and better filter the good from bad.

The project consists of two files:
* blog-scraper.py - Scrapes the TL blog section, saves the available info about the blogs and uses it to update the two rankings I maintained.
* blog_analysis.py - Basic analytics over the gathered collection.
