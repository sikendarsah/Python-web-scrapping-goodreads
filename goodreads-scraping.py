from time import sleep
from random import randint
from bs4 import BeautifulSoup
import requests
import pandas as pd
print('Libraries imported.')

home_url = 'https://www.goodreads.com'
booklist_url = home_url + '/list/show/7.Best_Books_of_the_21st_Century?page='
n_pages = 6

def fetch_list_pages(booklist_url, n_pages):
    pages_url = [booklist_url + str(i) for i in range(1,n_pages)]
    fetched_pages = []
    print("Fetching each page of the Goodreads' list:", end='')
    for pg_idx, page in enumerate(pages_url):
        page_response = requests.get(page).text
        fetched_pages.append(page_response)
        print(f'...{pg_idx+1}', end='')
        sleep(randint(2,15))  # to avoid overwhelming server
    print('\nAll webpages fetched.')
    return fetched_pages

def extract_book_urls(home_url, fetched_pages):
    print('Cooking soup.... extracting URL...')
    pages_soup = [BeautifulSoup(list_pg, 'lxml') for list_pg in fetched_pages]
    a_tags = [pg_soup.find_all(
        'a', {'class': 'bookTitle'}) for pg_soup in pages_soup]    
    book_urls = []
    for a_tag in a_tags:
        for half_url in a_tag:  # each tag contains partial book URL
            full_url = home_url + half_url['href']
            book_urls.append(full_url)
    print('Done.')
    return book_urls

def fetch_books_pages(book_urls):
    fetched_books = []
    print("Fetching each book's page:", end='')
    for url_idx, book_url in enumerate(book_urls):
        book_response = requests.get(book_url).text
        fetched_books.append(book_response)
        if url_idx > 0 and (url_idx+1)%10 == 0:
            print('.', end='')
        if url_idx > 0 and (url_idx+1)%10 == 0 and (url_idx+1)%100 == 0:
            print(f'{url_idx+1}', end='')
        sleep(randint(2,15))
    print(f"\nAll {len(fetched_books)} books' pages fetched.")
    return fetched_books

def extract_books_data(fetched_pages, fetched_books):
    print('Cooking soup.... extracting book details...')
    pages_soup = [BeautifulSoup(list_pg, 'lxml') for list_pg in fetched_pages]
    books_soup = [BeautifulSoup(book_pg, 'lxml') for book_pg in fetched_books]
    
    scores = []
    votes = []
    titles = []
    authors = []
    stars = []      # Average rating
    n_ratings = []  # Ratings count
    n_reviews = []  # Reviews count
    pages = []
    years = []
    genres = []
    
    for pg_soup in pages_soup:
        # Get book score and vote
        sv_tags = pg_soup.find_all('span', {'class': 'smallText uitext'})
        for sv_tag in sv_tags:
            score_txt = sv_tag.text.strip().split()[1].replace(',','')
            vote_txt = sv_tag.text.strip().split()[3].replace(',','')
            scores.append(int(score_txt))
            votes.append(int(vote_txt))
    
    for bk_soup in books_soup:     
        # Get book title 
        title_txt = bk_soup.find_all('h1', {'id': 'bookTitle'})[0].text
        titles.append(title_txt.strip())
        # Get name of author
        author_txt = bk_soup.find_all('a', {'class': 'authorName'})[0].text
        authors.append(author_txt.strip())
        # Get rating
        star_txt = bk_soup.find_all('span', {'itemprop': 'ratingValue'})[0].text
        stars.append(float(star_txt.strip()))
        # Get number of pages
        try:
            page_txt = bk_soup.find_all(
                'span', {'itemprop': 'numberOfPages'})[0].text
        except IndexError:
            page_txt = '0'  # If num of pages not found
        pages.append(int(page_txt.strip().split()[0]))
        # Get book genre
        try:
            gen = []
            gen_tags = bk_soup.find_all(
                'a', {'class': 'actionLinkLite bookPageGenreLink'})
            for gen_tag in gen_tags:
                gen.append(gen_tag.text.strip())
        except IndexError:
            gen = 'N/A'
        genres.append(gen)
        # Get number of ratings and reviews
        div_bookmetas = []
        div_bookmeta = bk_soup.find_all(
            'div', {'class': 'uitext stacked', 'id': 'bookMeta'})[0]
        div_bookmetas.append(div_bookmeta)
        for div in div_bookmetas:
            rat_txt = div.find_all('a', {'class': 'gr-hyperlink'})[0].text
            rev_txt = div.find_all('a', {'class': 'gr-hyperlink'})[1].text
            n_ratings.append(int(rat_txt.strip().split()[0].replace(',','')))
            n_reviews.append(int(rev_txt.strip().split()[0].replace(',','')))
        # Get only the year from publication details
        div_publication = []
        publication_txt = bk_soup.find_all('div', {'class': 'row'})[1].text
        div_publication.append(publication_txt.strip().split())
        for publication in div_publication:
            if publication[1] == '(first':
                years.append(int(publication[-1].strip(')')))
            else:
                for txt in publication:
                    if '20' in txt and 'th' not in txt and ')' not in txt:
                        years.append(int(txt))

    df = pd.DataFrame({
        'score': scores,
        'vote': votes,
        'title': titles,
        'author': authors,
        'genre': genres,
        'star': stars,
        'n_rating': n_ratings,
        'n_review': n_reviews,
        'pages': pages,
        'year': years,
    })
    return df

fetched_pages = fetch_list_pages(booklist_url, n_pages)
book_urls = extract_book_urls(home_url, fetched_pages)
fetched_books = fetch_books_pages(book_urls)
df = extract_books_data(fetched_pages, fetched_books)
df.head()
df.to_csv('Best-Books-of-the-21st-Century-v1.csv', index=False)