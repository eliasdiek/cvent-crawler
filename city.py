import urllib.request
from bs4 import BeautifulSoup
from urllib.error import HTTPError
import math
import csv

baseUrl = "https://www.cvent.com"

def get_html(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req)

    return html

def getSuppliersUrl(path):
    temp = path.split('/')
    idx = temp[3].split('-')[3]
    newMask = temp[2].replace('guide', 'meeting-hotels-')
    suppliersUrl = baseUrl + '/rfp/' +newMask + idx

    return suppliersUrl

def getPageInfo(obj):
    number_of_pages = 1
    try:
        pageTags = obj.find('div',{'id':'pagination'}).select('a')
        number_of_pages = len(pageTags) - 2
    except:
        number_of_pages = 1

    return number_of_pages

def convertUrl(url):
    pgUrl = url
    temp = url.split('.')
    temp.reverse()
    pgUrl = temp[3] + '.' + temp[2] + '.' + temp[1] + '-' + '2.' + temp[0] + '?so=1'
    print(pgUrl)

def getCityUrls(state, url):
    html = get_html(url)
    bsObject = BeautifulSoup(html, "lxml")
    number_of_pages = getPageInfo(bsObject)
    cityUrls = []

    for index in range(0, number_of_pages):
        if(index != 0):
            pgUrl = url
            splitter = url.split('.')
            splitter.reverse()
            page = index + 1
            pgUrl = splitter[3] + '.' + splitter[2] + '.' + splitter[1] + '-' + str(page) + '.' + splitter[0] + '?so=1'
            html = get_html(pgUrl)
            pgObject = BeautifulSoup(html, "lxml")
        else:
            pgObject = bsObject

        for index, item in enumerate(pgObject.select("div[itemprop=itemListElement]")):
            name = item.find('span',{'itemprop':'name'}).text.strip()
            link = getSuppliersUrl(item.find('a',{'itemprop':'URL'}).get('href'))
            temp = { 'state': state, 'city': name, 'link': link }
            cityUrls.append(temp)
    
    return cityUrls

def get_pageURL(link, page):
    temp = link.split('-')
    pgUrl = temp[0] + '-'  + temp[1] + '-' + temp[2] + '-'  + temp[3] + '-' + str(page) + '-' + temp[4] + '?so=1'
    
    return pgUrl

def get_hotels_url(cityUrls):
    hotelUrls = []

    for city_url in cityUrls:
        try:
            html = get_html(city_url['link'])
            bsObject = BeautifulSoup(html, "lxml")

            number_of_pages = getPageInfo(bsObject)
                
            for index in range(0, number_of_pages):
                page = index + 1
                pageUrl = get_pageURL(city_url['link'], page)

                if(page == 1):
                    pgObj = bsObject
                else:
                    html = get_html(pageUrl)
                    pgObj = BeautifulSoup(html, "lxml")
                
                for aElem in pgObj.select('a[itemprop=URL]'):
                    link = baseUrl + aElem.get('href')
                    name = aElem.find('span', {'itemprop':'name'}).text.strip()
                    hotelUrl = { 'name': name, 'link': link }
                    hotelUrls.append(hotelUrl)
                
        except HTTPError as e:
            content = e.read()
            text = open('error.txt', 'a')
            text.write(str(content))

    return hotelUrls


def main():
    url = "https://www.cvent.com/rfp/oregon-meeting-event-planning.aspx"
    cityUrls = getCityUrls('Florida', url)

    hotelUrls = get_hotels_url(cityUrls)
    for index, hotel in enumerate(hotelUrls):
        print(index, hotel['name'], hotel['link'])

if __name__ == '__main__':
    main()
