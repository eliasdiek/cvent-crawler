import urllib.request
from bs4 import BeautifulSoup
from urllib.error import HTTPError
import math
import csv
import re
import os
import pandas as pd

baseUrl = "https://www.travelweekly.com"

def getHtml(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req)

    return html


def getImgLinks(url):
    try:
        html = getHtml(url)
        bsObject = BeautifulSoup(html, "lxml")
        imgContainer = bsObject.find('div', {'id':'carousel-thumbnails'})
        imgLinks = []

        if(imgContainer != None):
            for imgTag in imgContainer.find('div', {'role':'listbox'}).select('img'):
                imgLink = imgTag.get('src').replace('160/90', '780/437')
                imgLinks.append(imgLink)
    except:
        imgLinks = []
    
    return imgLinks


def downloadImages(directory, url):
    imgLinks = getImgLinks(url)

    if(len(imgLinks)):
        for index, link in enumerate(imgLinks):
            try:
                opener = urllib.request.build_opener()
                opener.addheaders = [('User-agent', 'Mozilla/5.0')]
                urllib.request.install_opener(opener)
                urllib.request.urlretrieve(link, directory + '/' + str(index) + '.jpg')
            except:
                print('image not downloadable')

        return len(imgLinks)
    else:
        return len(imgLinks)

def find_nextSibling(bsObject, ref, tag = 'span', flag = 1):
    result = ''
    try:
        result = bsObject.find(tag, text=ref).nextSibling.strip()
    except:
        if(flag == 1):
            result = None
        else:
            result = "None"

    return result

def decodeEmail(e):
    de = ""
    k = int(e[:2], 16)

    for i in range(2, len(e)-1, 2):
        de += chr(int(e[i:i+2], 16)^k)

    return de

def getAddr(bsObject):
    addr = ''
    try:
        addrElem = bsObject.find('div', {'class':'address'})
        addrElem.a.extract()
        addrElem.br.replace_with(' ')
        addrElem.br.replace_with(' ')
        addr = addrElem.text.strip()
    except:
        addr = None

    return addr


def getCapacities(obj):
    result = ''
    objArr = obj.find('span', text="Capacities:").find_next_sibling('ul').select('li')
    for index, li in enumerate(objArr):
        result += li.text.strip()
        if(index < len(objArr) - 1):
            result += '|'

    return result
    

def getMeetingRooms(targetObj):
    titleArray = targetObj.select('h3.title-m.text-cursive')

    pattern = r"Meeting Room"
    repatter = re.compile(pattern)

    meeting_rooms = ''
    for index, titleObj in enumerate(titleArray):
        if(repatter.search(titleObj.text.strip()) != None):
            obj = targetObj.select('h3.title-m.text-cursive')[index].find_next_sibling('div', {'class': 'row'})
            meeting_rooms += titleObj.text.strip() + "=location>" + find_nextSibling(obj, 'Location:', 'span', 0) + "," + \
                            "flooring>" + find_nextSibling(obj, 'Flooring:', 'span', 0) + "," + \
                            "portable_walls_available>" + find_nextSibling(obj, 'Portable Walls Available:', 'span', 0) + "," + \
                            "size>" + find_nextSibling(obj, 'Size:', 'span', 0) + "," + \
                            "dimensions>" + find_nextSibling(obj, 'Dimensions:', 'span', 0) + "," + \
                            "capacities>" + getCapacities(obj)
            if(index < len(titleArray) - 1):
                meeting_rooms += '::'
    
    return meeting_rooms


def getNearbyAirports(obj):
    result = ''
    try:
        pattern = r"Nearby Airports"
        repatter = re.compile(pattern)
        titleArray = obj.select('h3.title-m')

        target_index = 0
        for index, item in enumerate(titleArray):
            if(repatter.search(item.text.strip()) != None):
                target_index = index
                break

        targetObjArr = obj.select('h3.title-m')[target_index].find_next_sibling('div').select('div.list li')
        for index, targetObj in enumerate(targetObjArr):
            result += targetObj.text.strip()
            if(index < len(targetObjArr) - 1):
                result += ','
    except:
        result = None

    return result


def grabDetails(state, city, url):
    html = getHtml(url)
    bsObject = BeautifulSoup(html, 'lxml')

    details = {}
    
    # Overview
    details['city'] = city
    details['ref_url'] = url
    details['name'] = bsObject.find('h1', {'class':'title-xxxl'}).text.strip()
    try:
        details['overview'] = bsObject.find('h2', text='Overview').find_next_sibling('p').text.strip()
    except:
        details['overview'] = None
    details['address'] = getAddr(bsObject)
    try:
        details['phone'] = find_nextSibling(bsObject, 'Phone:', 'b')
    except:
        details['phone'] = None
    try:
        details['fax'] = find_nextSibling(bsObject, 'Fax:', 'b')
    except:
        details['fax'] = None
    try:
        details['toll_free'] = find_nextSibling(bsObject, 'Toll Free:', 'b')
    except:
        details['toll_free'] = None

    details['number_of_images'] = 0
    details['alias'] = url.split('/')[4]
    try:
        directory = './results/images/' + state + '/' + details['alias'] + '/' + details['name'].replace("/", "-")
        if not os.path.exists(directory):
            os.makedirs(directory)
        details['number_of_images'] = downloadImages(directory, url)
    except:
        details['number_of_images'] = 0

    try:
        details['hotel_website'] = bsObject.find('a', {'title':'Hotel Website'}).get('href')
    except:
        details['hotel_website'] = None
    try:
        details['hotel_mail'] = decodeEmail(bsObject.find('a', {'title':'Hotel E-mail'}).get('href').split('#')[1])
    except:
        details['hotel_mail'] = None

    try:
        details['classification'] = bsObject.find('span', {'class':'number'}).text.strip() + ' ' + bsObject.find('span', {'class':'number'}).nextSibling.strip()
    except:
        details['classification'] = None

    try:
        details['commission'] = bsObject.find('td', {'class': 'comm'}).text.strip()
    except:
        details['commission'] = None
    try:
        details['rooms'] = bsObject.find('td',{'class':'rooms'}).text.strip()
    except:
        details['rooms'] = None
    try:
        details['rates'] = bsObject.find('td', {'class': 'rates'}).text.strip()
    except:
        details['rates'] = None

    # Details
    details['year_of_built'] = find_nextSibling(bsObject, 'Year Built:')
    details['year_last_renovated'] = find_nextSibling(bsObject, 'Year Last Renovated:')
    details['check_in_time'] = find_nextSibling(bsObject, 'Check in Time:')
    details['check_out_time'] = find_nextSibling(bsObject, 'Check out Time:')
    details['number_of_floors'] = find_nextSibling(bsObject, 'Number of Floors:')
    try:
        chain = bsObject.find('span', text='Chain:').find_next_sibling('a')
        details['chain_text'] = chain.text.strip()
        details['chain_link'] = baseUrl + chain.get('href')
        try:
            details['chain_website'] = bsObject.find('span', text='Chain Website:').find_next_sibling('a').get('href')
        except:
            details['chain_website'] = None
    except:
        details['chain_text'] = None
        details['chain_link'] = None

    # GDS Codes
    details['amadeus_gds'] = find_nextSibling(bsObject, 'Amadeus GDS:')
    details['galileo_apollo_gds'] = find_nextSibling(bsObject, 'Galileo/Apollo GDS:')
    details['sabre_gds'] = find_nextSibling(bsObject, 'Sabre GDS:')
    details['worldspan_gds'] = find_nextSibling(bsObject, 'WorldSpan GDS:')

    # Rates & Policies
    details['rate_policy'] = find_nextSibling(bsObject, 'Rate Policy:')
    details['standard_room'] = find_nextSibling(bsObject, 'Standard Room:')
    details['suite'] = find_nextSibling(bsObject, 'Suite:')
    details['credit_cards'] = find_nextSibling(bsObject, 'Credit Cards:')
    details['reservation_policy'] = find_nextSibling(bsObject, 'Reservation Policy:')
    details['deposit_policy'] = find_nextSibling(bsObject, 'Deposit Policy:')
    details['included_meals'] = find_nextSibling(bsObject, 'Included Meals:')
    details['cancellation_policy'] = find_nextSibling(bsObject, details['name'] + ' Cancellation Policy:')
    try:
        details['discounts_offered'] = ''
        itemArr = bsObject.find('span', text='Discounts offered:').find_next_sibling('ul').select('li')
        for index, discounts_item in enumerate(itemArr):
            details['discounts_offered'] += discounts_item.text.strip()
            if(index < len(itemArr) - 1):
                details['discounts_offered'] += ','
    except:
        details['discounts_offered'] = None

    # Room Amenities
    try:
        details['amenities'] = ''
        itemArr = bsObject.find('p', text="Amenities are in all rooms unless noted otherwise.").find_next_sibling('div').select('li')
        for index, amenity in enumerate(itemArr):
            details['amenities'] += amenity.text.strip()
            if(index < len(itemArr) - 1):
                details['amenities'] += ','
    except:
        details['amenities'] = None
    
    #Recreation
    try:
        details['on_site_activities'] = ''
        itemArr = bsObject.find('li', text='On-Site Activities').find_next_siblings('li')
        for index, activity in enumerate(itemArr):
            details['on_site_activities'] += activity.text.strip()
            if(index < len(itemArr) - 1):
                details['on_site_activities'] += ','
    except:
        details['on_site_activities'] = None

    try:
        details['nearby_activities'] = ''
        itemArr = bsObject.find('li', text='Nearby Activities').find_next_siblings('li')
        for index, activity in enumerate(itemArr):
            details['nearby_activities'] += activity.text.strip()
            if(index < len(itemArr) - 1):
                details['nearby_activities'] += ','
    except:
        details['nearby_activities'] = None

    # Services & Facilities
    try:
        details['guest_services'] = ''
        itemArr = bsObject.find('li', text='Guest Services').find_next_siblings('li')
        for index, activity in enumerate(itemArr):
            details['guest_services'] += activity.text.strip()
            if(index < len(itemArr) - 1):
                details['guest_services'] += ','
    except:
        details['guest_services'] = None

    try:
        details['security_services'] = ''
        itemArr = bsObject.find('li', text='Security Services').find_next_siblings('li')
        for index, activity in enumerate(itemArr):
            details['security_services'] += activity.text.strip()
            if(index < len(itemArr) - 1):
                details['security_services'] += ','
    except:
        details['security_services'] = None

    # meeting rooms and events
    try:
        meetings_tab_url = baseUrl + bsObject.find('a', text='Meetings Rooms & Events').get('href')
        html = getHtml(meetings_tab_url)
        meetings_bsObject = BeautifulSoup(html, "lxml")

        try:
            details['meeting_capacity'] = find_nextSibling(meetings_bsObject, 'Meeting Capacity:')
        except:
            details['meeting_capacity'] = None
        try:
            details['meeting_space'] = find_nextSibling(meetings_bsObject, 'Meeting Space:')
        except:
            details['meeting_space'] = None
        try:
            details['exhibit_space'] = find_nextSibling(meetings_bsObject, 'Exhibit Space:')
        except:
            details['exhibit_space'] = None
        try:
            details['largest_meeting_room_capacity'] = find_nextSibling(meetings_bsObject, 'Largest Meeting Room Capacity:')
        except:
            details['largest_meeting_room_capacity'] = None
        try:
            details['business_services'] = ''
            titleArray = meetings_bsObject.select('h3.title-m')
            pattern = r"Business Services"
            repatter = re.compile(pattern)
            
            for item in titleArray:
                if(repatter.search(item.text.strip()) != None):
                    matched = item.text.strip()
                    break

            service_arr = meetings_bsObject.find('h3', text=matched).find_next_sibling('div').select('div.list li')
            for index, service_item in enumerate(service_arr):
                details['business_services'] += service_item.text.strip()
                if(index < len(service_arr) - 1):
                    details['business_services'] += ','
        except:
            details['business_services'] = None

        #local info
        local_tab_url = baseUrl + bsObject.find('a', text='Local Info').get('href')
        html = getHtml(local_tab_url)
        local_bsObject = BeautifulSoup(html, "lxml")

        try:
            details['location_neighborhood_description'] = local_bsObject.find('h2', {'class':'title-m'}).find_next_sibling('p').text.strip()
        except:
            details['location_neighborhood_description'] = None
        try:
            details['nearest_cross_street'] = local_bsObject.find('strong', text="Nearest Cross Street:").nextSibling.strip()
        except:
            details['nearest_cross_street'] = None
        try:
            details['hotel_location'] = local_bsObject.find('strong', text="Hotel Location:").nextSibling.strip()
        except:
            details['hotel_location'] = None
        pattern = r"(Onsite)"
        repatter = re.compile(pattern)
        details['dining_options'] = ''
        try:
            optionsArr = local_bsObject.select('div.list li')
            for optionsItem in optionsArr:
                if(repatter.search(optionsItem.text.strip()) != None):
                    details['dining_options'] += optionsItem.text.strip() + ','
        except:
            details['dining_options'] = None

        details['nearby_airports'] = getNearbyAirports(local_bsObject)

        scriptTags = meetings_bsObject.select('script')
        number_of_tags = len(scriptTags)
        target_tag_string = scriptTags[number_of_tags - 1].text.strip()
        tempArr = target_tag_string.split(',')
        details['coordinates'] = tempArr[1] + ',' +  tempArr[2]

        details['meeting_rooms'] = getMeetingRooms(meetings_bsObject)
    except:
        details['meeting_capacity'] = None
        details['meeting_space'] = None
        details['exhibit_space'] = None
        details['largest_meeting_room_capacity'] = None
        details['business_services'] = None

        #local info
        local_tab_url = baseUrl + bsObject.find('a', text='Local Info').get('href')
        html = getHtml(local_tab_url)
        local_bsObject = BeautifulSoup(html, "lxml")

        try:
            details['location_neighborhood_description'] = local_bsObject.find('h2', {'class':'title-m'}).find_next_sibling('p').text.strip()
        except:
            details['location_neighborhood_description'] = None
        try:
            details['nearest_cross_street'] = local_bsObject.find('strong', text="Nearest Cross Street:").nextSibling.strip()
        except:
            details['nearest_cross_street'] = None
        try:
            details['hotel_location'] = local_bsObject.find('strong', text="Hotel Location:").nextSibling.strip()
        except:
            details['hotel_location'] = None
        pattern = r"(Onsite)"
        repatter = re.compile(pattern)
        details['dining_options'] = ''
        try:
            optionsArr = local_bsObject.select('div.list li')
            for optionsItem in optionsArr:
                if(repatter.search(optionsItem.text.strip()) != None):
                    details['dining_options'] += optionsItem.text.strip() + ','
        except:
            details['dining_options'] = None

        details['nearby_airports'] = getNearbyAirports(local_bsObject)

        scriptTags = local_bsObject.select('script')
        number_of_tags = len(scriptTags)
        target_tag_string = scriptTags[number_of_tags - 1].text.strip()
        tempArr = target_tag_string.split(',')
        details['coordinates'] = tempArr[2] + ',' +  tempArr[3]

        details['meeting_rooms'] = None

    return details


def main(name):
    urls = pd.read_csv("./hotel_links/" + name + '.csv')

    result = []
    for i in range(0, len(urls)):
        try:
            result.append(grabDetails(name, urls.City[i], urls.Link[i]))
        except:
            text = open('error.log', 'a')
            text.write(urls.City[i] + ',' + urls.Link[i])
            text.write('\n')

    directory = './results/csv'
    if not os.path.exists(directory):
        os.makedirs(directory)

    df = pd.DataFrame(result)
    df.to_csv(directory + '/' + name + '.csv',index=False)


if __name__ == '__main__':
    path = "./hotel_links"
    file_list = os.listdir(path)

    for file in file_list:
        file = file.replace('.csv', '')
        main(file)