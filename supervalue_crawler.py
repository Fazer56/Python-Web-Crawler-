from urllib.request import Request
import urllib.parse
import requests

import urllib.error
from urllib.request import urlopen as myReq
from urllib.error import HTTPError
from urllib.error import URLError
import pymysql.cursors
import ssl
import json
from bs4 import BeautifulSoup as soup
import re


class Database:
    def __init__(self):
        self.host = "127.0.0.1"
        self.username = "root"
        self.password = "Faoilean56"
        self.database = "foodie_db"
        self.port = 3306

        #self.host = "us-cdbr-iron-east-01.cleardb.net"
        #self.username = "bdfcffaa39b81f"
        #self.password = "6560d5a4"
        #self.database = "heroku_7a83733ae13fe14"

    def connection(self):
        connection = pymysql.connect(host=self.host,
                                     user=self.username,
                                     password=self.password,
                                     port=self.port,
                                     db=self.database,
                                     cursorclass=pymysql.cursors.DictCursor)
        return connection


######## Crawler for one page #######################

class App:

    # name = Premium Irish Eating Apple (1 Piece)
    # subcategory = apple
    # category = fruit
    # brand = "tescos finest"
    # quantity = 4
    # price = 4.00
    # pricePerKg = 20.00 per kg
    # pricePerUnit = 0.55

    # constructor
    def __init__(self, name, brand, price, pricePerKg, pricePerUnit, quantity, subcategory, category, links):
        self.name = name
        self.brand = brand
        self.price = price
        self.pricePerKg = pricePerKg
        self.pricePerUnit = pricePerUnit
        self.quantity = quantity
        self.subcategory = subcategory
        self.category = category
        self.links = links

    # print out the information found
    def __str__(self):
        return ("Name: " + self.name.encode('UTF-8') +
                "\r\nBrand: " + self.brand.encode('UTF-8') +
                "\r\nPrice: " + self.price.encode('UTF-8') +
                "\r\nPrice Per Kg: " + self.pricePerKg.encode('UTF-8') +
                "\r\nPrice Per Unit: " + self.pricePerUnoit.encode('UTF-8') +
                "\r\nSub Category: " + self.subcategory.encode('UTF-8') +
                "\r\nCategory: " + self.category.encode('UTF-8') + "\r\n")


class Scrape:

    def __init__(self, url):
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.url = url

    def getPage(self, url):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        start_page = Request(url, headers=self.headers)

        uClient = myReq(start_page, context=ctx)
        page_html = uClient.read()
        uClient.close()
        page_soup = soup(page_html, "html.parser")

        return page_soup

    def crawl(self):
        # requests library sends GET request to the url which returns the
        # page information
        # For ignoring SSL certificate errors
        #target_pages = page_soup.find_all("a", {"class": "cat pill ajax-link"})
        page_soup = self.getPage(self.url)
        target_menu = page_soup.find("div", {"class": "menu-inner"})
        target_div = target_menu.find_all("a")

        for a in target_div:
            try:
                print(a["data-url"])
                #pass the url found in the menu to the getPages function
                targ_page = self.getPage(a["data-url"])
                targ_men = targ_page.find("div", {"class": "category-listing-navigation-pills"})
                links = targ_men.find_all("a", {"class": "cat pill ajax-link"})

                for x in links:
                    targ_page = self.getPage(x["href"])
                    try:
                        sub = targ_page.find("span", {"class": "subcat-name"})
                        if "inactive" in sub['class']:
                            self.skrape(targ_page, x["href"])


                    except TypeError:
                        targ_men = targ_page.find("div", {"class": "category-listing-navigation-pills"})
                        inner_links = targ_men.find_all("a", {"class": "cat pill ajax-link"})

                        for y in inner_links:
                            inner_targ_page = self.getPage(y["href"])
                            self.skrape(inner_targ_page, x["href"])
                        print("OOPSYY")



            except KeyError:
                print("No data")

        #target_pages = target_div.find_all("a", {"class": "see-all-btn"})





    def skrape(self, page, url):
        products = page.find_all("div", {"class": "col-xs-6 col-sm-4 col-md-2-4 ga-impression ga-product"})

        productsPriceSpan = page.find_all("span", {"class": "product-details-price-per-kg"})

        try:
            category = re.search('shopping/(.+?)/c-', url).group(1)
            print(category)
        except AttributeError:
            # if the category is not found in the url found in the original string
            category = ''

        for pr, pType in zip(products, productsPriceSpan):
            j = json.loads(pr['data-product'])

            priceType = ""
            pricePerKg = "0.0"
            prod = pType["data-price-per-kg"]
            if "each" in prod:
                priceType = "each"
                pricePerKg = prod
            else:
                priceType = "per kilo"
                pricePerKg = prod

            if "/" in pricePerKg:
                pkg_num = pricePerKg.split("/")
                if len(pkg_num) > 0:
                    kg_price = pkg_num[0].replace('€', '')
                else:
                    kg_price = ""
            else:
                pkg_num = pricePerKg.split()
                if len(pkg_num) > 0:
                    kg_price = pkg_num[0].replace('€', '')
                else:
                    kg_price = ""

            print("INSERT INTO TABLE Products(Id, Supermarket, Name, Price, SubCategory, Category, PriceType,"
                  " PricePerKg)\nVALUES(" + j["id"] + ", " + "Supervalue, " + j["name"] + ", " + j["price"] + ", "
                  + j["category"] + ", " + category + ", " + priceType + ", " + kg_price + ");")

            insert_string = "INSERT INTO TABLE Products(Supermarket, Name, Price, SubCategory, Category, PriceType, " \
                            "PricePerKg) \nVALUES(Supervalue, " + j["name"] + ", " + j["price"] \
                            + ", " + j["category"] + ", " + category + ", " + priceType + ", " + pricePerKg + ");"

            self.db_insert("Supervalue", j["name"], j["price"], j["category"], category, priceType, kg_price)

    def db_insert(self, supermarket, name, price, subcategory, category, price_type, price_perkg):
        db = Database()
        connection = db.connection()

        try:
            with connection.cursor() as cursor:
                sql_query = "INSERT INTO products(`Supermarket`, `ProductName`, `Price`, `PriceKg`, `PriceType`, " \
                            "`SubCategory`, `Category`) VALUES(%s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql_query, (supermarket, name, float(price), price_perkg, price_type, subcategory, category))
                connection.commit()
        finally:
            connection.close()


scraper = Scrape("https://shop.supervalu.ie/shopping/fruit-vegetables/c-150100001")

scraper.crawl()

        

