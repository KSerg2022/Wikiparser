"""Main module."""
import re
from time import sleep, time

from utils.calc_time import calc_time
from db.db_postgres import (main as init_db,
                            insert_data_in_table_link,
                            insert_data_in_table_link_to_link, )
from db.db_operations import (get_id_for_link,
                              get_id_for_title_article,
                              get_urls_from_start_url,
                              get_query,
                              get_mean_value_of_second_level_descendants,
                              get_title_article,
                              get_check_title_article,
                              get_check_parent_title_article)
from main.parcer import get_links
from main.display_result import maim as print_results
from settings import wiki_link
from utils.calc_time import calc_delay


def get_page_by_link(links: list[str],
                     limit_per_minute: int,
                     finish_article: str) -> tuple | bool:
    """
    Find link to article with title - in variable 'finish_article'
    :param links: list of links for queries,
    :param limit_per_minute: request per minute limit,
    :param finish_article: title of article on which is stopping finding,
    :return: True if result found, False if result not found.
    """
    for link in links:
        current_time = time()
        delay = calc_delay(limit_per_minute, current_time)
        sleep(delay)

        links = get_links(link)
        link_name, links_and_title = find_article_name_on_page(links, finish_article=finish_article)
        if link_name:

            insert_data_in_table_link(link_name)

            id_start_link = get_id_for_link(link)
            id_links = get_id_for_link(link_name)
            data_for_table_link_to_link = list(zip(id_start_link * len(id_links), id_links))
            insert_data_in_table_link_to_link(data_for_table_link_to_link)
            return link_name

    return False


def find_finish_article(data_links: list[str], finish_article: str) -> str:
    """
    Find link in line where which contain text according to regular expression with variable 'finish_article'
    :param data_links: list of links (tag <a>),
    :param finish_article: title of article link to find,
    :return: link (tag <a>) which contain regular expression, or empty string.
    """
    for link in data_links:
        pattern = re.compile(f'{finish_article}')
        result = pattern.findall(str(link[1]))
        if result:
            # return link[0]
            return link
    return ''


def find_article_name_on_page(start_url: str, finish_article: str) -> tuple[str, list[str]] | tuple[bool, list[str]]:
    """
    Find link which to go to finish article.
    :param start_url: link to article from which are start find,
    :param finish_article: title of article on which is stopping finding,
    :return: If found - link (tag <a>) and False, if not found - False and list of links (tag <a>).
    """
    links = get_links(start_url)

    link_to_finish_article = find_finish_article(links, finish_article)
    if link_to_finish_article:
        return link_to_finish_article, links
    else:
        return False, links


def print_results_for_task(title_articles: list[str]):
    """
    Output results according to task.
    :param title_articles: Title of articles - start, intermediate, finish article,
    """
    most_popular_articles = get_query('most_popular_articles')
    articles_with_most_links = get_query('articles_with_most_links')
    mean_value_of_second_level_descendants = get_mean_value_of_second_level_descendants(title_articles[0])
    print_results(title_articles,
                  most_popular_articles,
                  articles_with_most_links,
                  mean_value_of_second_level_descendants)


def find_result(start_article, finish_article, requests_per_minute):
    """
    Are looking for the titles of articles by moving on which you can get from the start article to the finish.
    :param start_article: title of article from which start find,
    :param finish_article: title of article on which is stopping finding,
    :param requests_per_minute: request per minute limit,
    :param links_per_page: maximum number of links that are taken from the page,
    :return: If found - True, if not found - False.
    """
    start_url = f'{wiki_link}{start_article}'
    link, links_and_title = find_article_name_on_page(start_url, finish_article)
    add_data_to_db(start_article, start_url, links_and_title)
    if link:
        return link

    else:
        links = get_urls_from_start_url(start_url)
        link = get_page_by_link(links, limit_per_minute=requests_per_minute, finish_article=finish_article)
        if link:
            return link
    return False


def add_data_to_db(start_article: str, start_url: str, links: list[tuple]):
    """
    Adding data to database.
    :param start_article: title of article from which start find,
    :param start_url: link to article from which are start find,
    :param uniq_data_teg_a: list of links (tag <a>)
    :param links_per_page: maximum number of links that are taken from the page,
     """
    insert_data_in_table_link((start_url, start_article))
    insert_data_in_table_link(links)

    try:
        id_start_link = get_id_for_title_article(start_article)
    except TypeError:
        id_start_link = get_id_for_link(start_url)

    id_links = get_id_for_link(links)
    data_for_table_link_to_link = list(zip(id_start_link * len(id_links), id_links))
    insert_data_in_table_link_to_link(data_for_table_link_to_link)


def get_result_from_db(start_article: str, finish_article: str) -> bool | list[str]:
    """
    Get result from start_article to finish_article in database, and is there a transition path.
    :param start_article: title of article from which start find,
    :param finish_article: title of article on which is stopping finding,
    :return: if found - list of title articles from start to end, if not found - False.
    """
    total_result = []
    start_title_article = get_check_title_article(start_article)
    finish_title_article = get_check_title_article(finish_article)
    if not start_title_article or not finish_title_article:
        return False

    total_result.append(finish_title_article[0])

    way_from_start_to_finish_article = get_way_from_start_to_finish_article(start_title_article,
                                                                            total_result)
    if way_from_start_to_finish_article:
        return way_from_start_to_finish_article
    return False


def get_way_from_start_to_finish_article(start_title_article, total_result, time_data=None):
    """"""
    if not time_data:
        time_data = []

    while True:
        parent_title_articles = get_check_parent_title_article(total_result[-len(total_result)])
        if not parent_title_articles:
            return False

        if start_title_article[0] in parent_title_articles:
            total_result.insert(0, start_title_article[0])
            return total_result
        else:
            for article in parent_title_articles:
                if article in total_result or article in time_data:
                    continue

                time_data.append(article)
                total_result.insert(0, article)
                way_from_start_to_finish_article = get_way_from_start_to_finish_article(start_title_article,
                                                         total_result,
                                                         time_data=time_data)
                if way_from_start_to_finish_article:
                    return total_result
                else:
                    total_result.pop(0)


def find_way_to_finish_article(start_article, finish_article, requests_per_minute, links_per_page, time_data=None):
    """
    Find way from start_article to finish_article.
    :param start_article: title of article from which find way
    :param finish_article: title of article on which is stopping finding,
    :param requests_per_minute: request per minute limit
    :param links_per_page: maximum number of links that are taken from the page
    :return: ! add comment.
    """
    if not time_data:
        time_data = set()

    title_articles = [start_article]
    title_articles.extend(get_urls_from_start_url(f'{wiki_link}{start_article}', article=True))
    for title_article in title_articles[:links_per_page]:
        if title_article in time_data:
            continue

        total_result = find_result(title_article, finish_article, requests_per_minute)
        if total_result:
            return total_result

        time_data.add(title_article)

    for title_article in title_articles:
        total_result = find_way_to_finish_article(title_article, finish_article, requests_per_minute, links_per_page,
                                                  time_data=time_data)
        if total_result:
            return total_result
    return []


@calc_time
def main(start_article, finish_article, requests_per_minute=None, links_per_page=None):
    """Main controller."""
    init_db()

    if total_result := get_result_from_db(start_article, finish_article):
        print_results_for_task(total_result)
        return total_result

    else:
        total_result = find_way_to_finish_article(start_article,
                                                  finish_article,
                                                  requests_per_minute,
                                                  links_per_page)
        if total_result:
            total_result = get_result_from_db(start_article, finish_article)
            print_results_for_task(total_result)
            return total_result

        print('Can not find result.')
        return []
