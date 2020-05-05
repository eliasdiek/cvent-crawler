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


def get_states_url(html):
    bsObject = BeautifulSoup(html, "lxml")
    stateWrapper = bsObject.find('h2',text="Browse by State").find_next_sibling('ul')
    stateUrls = []

    for stateElem in stateWrapper.select('a'):
        name = stateElem.text.strip()
        link = baseUrl + stateElem.get('href')
        temp = { 'name': name, 'link': link }
        stateUrls.append(temp)
        with open('results/' + name + '.csv', 'w', newline='') as f:
            writer = csv.writer(f, delimiter =',')
            writer.writerow(('City', 'Link'))

    return stateUrls


def getSuppliersUrl(path):
    temp = path.split('/')
    idx = temp[3].split('-')[3]
    newMask = temp[2].replace('guide', 'meeting-hotels-')
    suppliersUrl = baseUrl + '/rfp/' +newMask + idx

    return suppliersUrl


def get_cities_url(stateUrls):
    cityUrls = []

    for state in stateUrls:
        html = get_html(state['link'])
        bsObject = BeautifulSoup(html, "lxml")
        number_of_pages = getPageInfo(bsObject)

        for index in range(0, number_of_pages):
            if(index != 0):
                pgUrl = state['link']
                splitter = state['link'].split('.')
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
                temp = { 'state': state['name'], 'city': name, 'link': link }
                cityUrls.append(temp)

    return cityUrls


def get_pageURL(link, page):
    temp = link.split('-')
    pgUrl = temp[0] + '-'  + temp[1] + '-' + temp[2] + '-'  + temp[3] + '-' + str(page) + '-' + temp[4] + '?so=1'
    
    return pgUrl


def getPageInfo(obj):
    number_of_pages = 1
    try:
        pageTags = obj.find('div',{'id':'pagination'}).select('a')
        number_of_pages = len(pageTags) - 2
    except:
        number_of_pages = 1

    return number_of_pages


def get_hotels_url(cityUrls):
    hotelUrls = []

    for city_url in cityUrls:
        file_name = 'results/' + city_url['state'] + '.csv'
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
                    hotelUrls.append(link)
                    write_hotels_csv(file_name, city_url['city'], link)
                
        except HTTPError as e:
            content = e.read()
            text = open('error.txt', 'a')
            text.write(str(content))

    return hotelUrls


def write_hotels_csv(file_name, city_name, link):
    with open(file_name, 'a', newline='') as f:
        writer = csv.writer(f, delimiter =',')
        writer.writerow((city_name, link))


def main():
    targetUrl = "https://www.cvent.com/rfp/united-states-meeting-event-planning.aspx"

    html = get_html(targetUrl)
    stateUrls = get_states_url(html)
    cityUrls = get_cities_url(stateUrls)
    hotelUrls = get_hotels_url(cityUrls)

    print(len(hotelUrls))

if __name__ == '__main__':
    main()