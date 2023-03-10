""""""
import psycopg2
from psycopg2 import Error

from db.data import tables
from settings import database_name as db_name


class DBConnection:
    """"""

    def __init__(self):
        """"""
        self.conn = psycopg2.connect(host='127.0.0.1',
                                     user='postgres',
                                     database=f'{db_name}',
                                     password='1qa2ws3ed',
                                     port='5432')
        self.cursor = self.conn.cursor()
        self.cursor.execute(tables[0])
        self.cursor.execute(tables[1])

    # def __del__(self):
    #     """"""
    #     self.conn.close()

    def add_links_to_db(self, links: list[tuple] | tuple):
        """"""
        if not isinstance(links, list):
            links = [links]
        for link in links:

            # print(link)

            try:
                insert_query = f"INSERT INTO links(link, title_article) VALUES {link};"
                self.cursor.execute(insert_query)
                self.conn.commit()
            except (Exception, Error) as error:
                # print(f'When adding data {link} in PostgresSQ {error}')
                self.conn.rollback()
                update_query = f"UPDATE links SET link = '{list(link)[0]}' WHERE title_article = '{list(link)[1]}'" \
                               f"AND NOT EXISTS (SELECT link FROM links WHERE link = '{list(link)[0]}')"

                # print(update_query)
                self.cursor.execute(update_query)
                self.conn.commit()

    def add_link_to_link(self, id_links: list[tuple] | tuple):
        """"""
        for link in id_links:
            try:
                insert_query = f'INSERT INTO link_to_link(link_left, link_right) VALUES {link}'
                self.cursor.execute(insert_query)
                self.conn.commit()
            except (Exception, Error) as error:
                # print(f'When adding data {link} in PostgresSQL {error}')
                self.conn.rollback()

    def delete_db(self):
        """"""
        self.cursor.execute('Delete from link_to_link')
        self.cursor.execute('Delete from links')
        self.conn.commit()

    def get_id_for_link(self, links: list[tuple] | tuple | str) -> list:
        """
        Searching id in database for link or links from list.
        :param links: list of links or a link to search for their id in the database,
        :return: list of id for link or links from list.
        """
        id_for_link = []
        if not isinstance(links, list):
            links = [links]
        for link in links:
            if isinstance(link, tuple):
                link = link[0]
            try:
                query = f"SELECT id FROM links WHERE link = '{link}'"
                self.cursor.execute(query)
            except (Exception, Error) as error:
                print(f'When searching for data {link} in PostgresSQ {error}')
                self.conn.rollback()
            else:
                id_link = self.cursor.fetchone()
                if not id_link:
                    continue
                else:
                    id_for_link.append(id_link[0])
        return id_for_link

    def get_id_for_title_article(self, title: str) -> list[str]:
        """
        Searching article's id in database by his title.
        :param title: title to search for their id in the database,
        :return: list of id for article with title.
        """
        id_article = []
        try:
            query = f"SELECT id FROM links WHERE title_article = '{title}'"
            self.cursor.execute(query)
        except (Exception, Error) as error:
            print(f'When searching for data {title} in PostgresSQ {error}')
            self.conn.rollback()
        else:
            id_result = self.cursor.fetchone()
            try:
                id_article.append(id_result[0])
            except:
                return []
        return id_article

    def get_urls_from_start_url(self, start_url: list[str] | str = None, article: str = None) -> list[str]:
        """
        Get a list of link's id, first-level descendants.
        :param start_url: initial link,
        :param article: If True - function return list of articles? if False - list of links,
        :return: list of ids for links, which are first-level descendants.
        """
        id_for_start_url = 0
        try:
            id_for_start_url = self.get_id_for_link(start_url)[0]
        except IndexError:
            pass
        try:
            id_for_start_url = self.get_id_for_title_article(article)[0]
        except IndexError:
            pass
        urls = []

        query = f"SELECT link, title_article FROM links " \
                f"WHERE links.id IN (SELECT link_right FROM link_to_link" \
                f" WHERE link_left = {id_for_start_url})"
        # if article:
        #     query = f"SELECT link, title_article FROM links " \
        #             f"WHERE links.id IN (SELECT link_right FROM link_to_link" \
        #             f" WHERE link_left = {id_for_start_url})"

        try:
            self.cursor.execute(query)
        except (Exception, Error) as error:
            print(f'When searching for data in  PostgresSQ {error}')
            self.conn.rollback()
        else:
            # for url in self.cursor.fetchall():
            #     urls.append(list(url)[0])
            urls = self.cursor.fetchall()

        # print(f'urls - {len(urls), urls[:3]}')

        return urls

    def get_title_article(self, title: str = None, url: str = None) -> list[str] | bool:
        """
        Get title for the article in database by url.
        :param url:  link to article in internet,
        :param title:
        :return: title for the article in database according url.
        """
        title_article = []

        # print(f'title - {title}, url - {url}')

        if title:
            query = f"SELECT title_article FROM links WHERE title_article = '{title}'"
        if url:
            query = f"SELECT title_article FROM links WHERE link = '{url}'"

        try:
            self.cursor.execute(query)
        except (Exception, Error) as error:
            print(f'When searching for data in PostgresSQ {error}')
            self.conn.rollback()
        else:
            title = self.cursor.fetchone()
            try:
                title_article.append(title[0])
            except Exception:
                return False

        return title_article

    def get_check_parent_title_article(self, title: str) -> list[str] | bool:
        """
        Checking if is article in database by title.
        :param title: title to article which myst find in internet,
        :return:  if is - title for the article in database according url, if not is - False.
        """
        title_article = []

        try:
            query = f"SELECT title_article FROM link_to_link, links " \
                    f"WHERE link_right = (SELECT id link FROM links " \
                    f"WHERE title_article = '{title}') " \
                    f"AND id = link_left"
            self.cursor.execute(query)
        except (Exception, Error) as error:
            print(f'When searching for data in PostgresSQ {error}')
            self.conn.rollback()
        else:
            title = self.cursor.fetchall()
            try:
                for value in title:
                    title_article.append(value[0])
            except Exception:
                pass

        return title_article