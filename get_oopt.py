from urllib.request import urlretrieve
from urllib.parse import quote
from urllib.request import urlopen
import time
import os
import re
import json
import glob
from datetime import datetime
from urllib import parse
import socket
import geopy as geopy

socket.setdefaulttimeout(15)

def file_age_in_days(file):
    try:
        mod_time = os.path.getmtime(file)
        file_last_mod = datetime.fromtimestamp(mod_time)
        return (datetime.now() - file_last_mod).days
    except FileNotFoundError:
        return 999


def safe_urlretrieve(url, file, attempts=10):
    if attempts == 0:
        print('   download fail: ' + url)
        return

    try:
        return urlretrieve(url, filename=file)
    except:
        print('   loading attempt: ' + str(attempts - 1))
        time.sleep(5)
        if attempts <= 3:
            time.sleep(30)
        if attempts == 1:
            time.sleep(180)
        return safe_urlretrieve(url, file, attempts=attempts - 1)


def get_list():
    if file_age_in_days('index.html') > 7:
        print('downloading index...')
        safe_urlretrieve('http://oopt.aari.ru/oopt', 'index.html')

    with open('index.html', 'r', encoding="utf-8") as index_file:
        index_page_text = index_file.read()

    # <a href="/oopt/%D0%BE%D0%B7%D0%B5%D1%80%D0%BE-%D0%91%D0%B5%D0%BB%D1%8F%D1%88">озеро Беляш</a>          </td>
    url_list = re.findall(r'            <a href="/oopt/(.+)">.+</a>          </td>', index_page_text)
    url_list = ['http://oopt.aari.ru/oopt/' + i for i in url_list]

    with open('list.txt', 'w') as list_file:
        list_file.write("\n".join(url_list))


def get_pages():
    os.makedirs('pages', exist_ok=True)

    with open('list.txt') as f:
        oopt_list = f.read().splitlines()

    #oopt_list = oopt_list[:20]
    print('List length: ' + str(len(oopt_list)))

    for i, url in enumerate(oopt_list):
        page_file = parse.unquote(url)
        page_file = 'pages\\' + page_file.replace('http://oopt.aari.ru/oopt/', '') + '.html'
        print(str(i) + ': ' + page_file.replace('pages\\', ''))

        if file_age_in_days(page_file) > 7:
            safe_urlretrieve(url, page_file)

def parse_pages():
    res_file = open("oopt.csv", 'w', encoding="utf-8")

    res_file.write('Название^'\
                   'Текущий статус ООПТ^'\
                   'Значение ООПТ^'\
                   'Профиль^'\
                   'Категория ООПТ^'\
                   'Тип^'\
                   'Дата создания^'\
                   'Федеральный округ^'\
                   'Регион^'\
                   'Муниципальное образование^'\
                   'Географическое положение^'\
                   'Описание границ^'\
                   'Входит в границы следующих ООПТ^'\
                   'Общая площадь ООПТ^'\
                   'Ссылка^'\
                   'Файл^'\
                   'Перечень основных объектов охраны^'\
                   'Природные особенности ООПТ\n')

    for file_name in glob.glob("pages/*.html"):
        res = ''

        with open(file_name, 'r', encoding="utf-8") as file:
            text = file.read()

        try:
            body = re.search('<h2>Установочные сведения(.*)', text, re.MULTILINE | re.DOTALL | re.UNICODE).group(1)
            body = text
        except:
            print('   parse error: ' + file_name)
            continue

        try:
            title = re.search('<h2 class="with-tabs">(.*?)</h2>', body, re.MULTILINE | re.DOTALL | re.UNICODE).group(1)
        except:
            title = ''

        try:
            link = re.search('<li class="active" ><a href="/oopt/(.*?)" class="active">Информация об ООПТ</a></li>', body,
                             re.MULTILINE | re.DOTALL | re.UNICODE).group(1)
            link = 'http://oopt.aari.ru/oopt/' + link
        except:
            link = ''

        try:
            federal_district_list = re.findall('lineage-item lineage-item-level-0">.*?">(.*?)</a></span>', body,
                               re.MULTILINE | re.DOTALL | re.UNICODE)
            federal_district_list = list(set(federal_district_list))

            if len(federal_district_list)==0:
                federal_district=''
            elif len(federal_district_list)==1:
                federal_district=federal_district_list[0]
            else:
                federal_district = ' + '.join(federal_district_list)
        except:
            federal_district = ''


        try:
            region_list = re.findall('lineage-item lineage-item-level-1">.*?">(.*?)</a></span>', body,
                               re.MULTILINE | re.DOTALL | re.UNICODE)
            region_list = list(set(region_list))

            if len(region_list)==0:
                region=''
            elif len(region_list)==1:
                region=region_list[0]
            else:
                region = ' + '.join(region_list)
        except:
            region = ''

        try:
            district_list = re.findall('lineage-item lineage-item-level-2">.*?">(.*?)</a></span>', body,
                               re.MULTILINE | re.DOTALL | re.UNICODE)
            district_list = list(set(district_list))

            if len(district_list)==0:
                district=''
            elif len(district_list)==1:
                district=district_list[0]
            else:
                district = ' + '.join(district_list)
        except:
            district = ''


        try:
            descr = re.search('Природные особенности ООПТ:&nbsp;</div>(.*?)</div>', body,
                              re.MULTILINE | re.DOTALL | re.UNICODE).group(1)
            descr = re.sub('<br />', ' ', descr)
            descr = re.sub('<[^>]*>', '', descr)
        except:
            descr = ''

        if descr == '':
            try:
                descr = re.search(
                    '<div class="field-label">Обоснование создания ООПТ и ее значимость.*?"field-item odd">(.*?)</div>',
                    body, re.MULTILINE | re.DOTALL | re.UNICODE).group(1)
                descr = re.sub('<br />', ' ', descr)
                descr = re.sub('<[^>]*>', '', descr)
            except:
                descr = ''

        try:
            location = re.search(
                '<div class="field-label">Географическое положение.*?<div class="field-item odd">(.*?)</div>', body,
                re.MULTILINE | re.DOTALL | re.UNICODE).group(1)
            location = re.sub('<br />', ' ', location)
            location = re.sub('<[^>]*>', '', location)
        except:
            location = ''

        try:
            boundaries = re.search(
                '<div class="field-label">Описание границ.*?<div class="field-items">(.*?)</div>', body,
                re.MULTILINE | re.DOTALL | re.UNICODE).group(1)
            boundaries = re.sub('<br />', ' ', boundaries)
            boundaries = re.sub('<[^>]*>', '', boundaries)
        except:
            boundaries = ''

        try:
            obj_category = re.search('Категория ООПТ:&nbsp;</div>(.*?)</div>', body,
                                     re.MULTILINE | re.DOTALL | re.UNICODE).group(1)
            obj_category = re.sub('<[^>]*>', '', obj_category)
        except:
            obj_category = ''

        try:
            obj_type = re.search('Тип:&nbsp;</div>(.*?)</div>', body, re.MULTILINE | re.DOTALL | re.UNICODE).group(1)
            obj_type = re.sub('<[^>]*>', '', obj_type)
        except:
            obj_type = ''

        try:
            in_obj = re.search('Входит в границы следующих ООПТ:&nbsp;</div>.*?<span class="field-content">(.*?)</span>',
                               body, re.MULTILINE | re.DOTALL | re.UNICODE).group(1)
            in_obj = re.sub('<[^>]*>', '', in_obj)
        except:
            in_obj = ''

        try:
            start_date = re.search('Дата создания:&nbsp;</div>(.*?)</div>', body,
                                   re.MULTILINE | re.DOTALL | re.UNICODE).group(1)
            start_date = re.sub('<[^>]*>', '', start_date)
        except:
            start_date = ''

        if start_date == '':
            try:
                start_date = re.search('Дата ликвидации (реорганизации):&nbsp;</div>(.*?)</div>', body,
                                       re.MULTILINE | re.DOTALL | re.UNICODE).group(1)
                start_date = re.sub('<[^>]*>', '', start_date)
            except:
                start_date = ''


        try:
            theme_list = re.findall('Профиль:&nbsp;</div>(.*?)</div>', body, re.MULTILINE | re.DOTALL | re.UNICODE)
            theme_list = [re.sub('<[^>]*>', '', i) for i in theme_list]
            theme_list = [re.sub('\s', '', i) for i in theme_list]
            theme_list = sorted(list(set(theme_list)))

            if len(theme_list)==0:
                theme=''
            elif len(theme_list)==1:
                theme=theme_list[0]
            else:
                theme = ' + '.join(theme_list)

        except:
            theme = ''

        try:
            status = re.search('Значение ООПТ:&nbsp;</div>(.*?)</div>', body, re.MULTILINE | re.DOTALL | re.UNICODE).group(1)
            status = re.sub('<[^>]*>', '', status)
        except:
            status = ''

        try:
            area = re.search('Общая площадь ООПТ:&nbsp;</div>(.*?)</div>', body,
                             re.MULTILINE | re.DOTALL | re.UNICODE).group(1)
            area = re.sub('<[^>]*>', '', area)
            area = re.sub('га', '', area)
        except:
            area = ''

        try:
            protected = re.search('Перечень основных объектов охраны:&nbsp;</div>(.*?)</div>', body,
                                  re.MULTILINE | re.DOTALL | re.UNICODE).group(1)
            protected = re.sub('<[^>]*>', '', protected)
        except:
            protected = ''

        try:
            actuality = re.search('Текущий статус ООПТ:&nbsp;</div>(.*?)</div>', body,
                                  re.MULTILINE | re.DOTALL | re.UNICODE).group(1)
            actuality = re.sub('<[^>]*>', '', actuality)
        except:
            actuality = ''

        line = title + '^' + actuality+ '^' + status + '^' + theme + '^' + obj_category + '^' + obj_type + '^' + start_date
        line += '^' + federal_district + '^' + region + '^' + district  + '^' + location + '^'  + boundaries + '^' + in_obj
        line += '^' + area + '^' + link  + '^' + file_name + '^' + protected + '^' + descr

        line = re.sub('\s+', ' ', line)
        line = line.replace(" ^", '^')
        line = line.replace("^ ", '^')

        line = line.replace("\n", ' ')
        res_file.write(line+'\n')

    res_file.close()


def yandex_geolocate(addr):
    url='http://geocode-maps.yandex.ru/1.x/?geocode='+quote(addr)+'&results=1&format=json'
    try:
        try:
            resp = urlopen(url)
        except:
            time.sleep(10)
            resp = urlopen(url)
        j_resp = json.loads(resp.read().decode(resp.info().get_param('charset') or 'utf-8'))
        kind = j_resp['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty']['GeocoderMetaData']['kind']
        coords = j_resp['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
        coords = (coords.split(' '))[::-1]
    except:
        kind=''
    if kind in ['locality', 'hydro', 'railway', 'route', 'vegetation', 'other', 'street']:
        return ', '.join(coords)
    else:
        return ''


def geolocate_by_description(descr):
    elems = descr.split('^')

    if len(elems[10])>0:
        addr=elems[10]  # Location
    elif len(elems[11])>0:
        addr=elems[11]  # Boundaries
    else:
        addr=elems[0]  # Title

    names = re.findall('([А-ЯЁ][a-zа-яё][a-zA-Zа-яА-ЯЁё\-]+)', addr, re.UNICODE)
    stop_list =['Западнее', 'Восточнее', 'Севернее', 'Южнее', 'От', 'Окр', 'На', 'Около', 'По', 'Северо-Западный',
                'Северо-Восточный', 'Юго-Западный', 'Юго-Восточный', 'Болото', 'Город', 'Широта', 'Долгота',
                'Роща', 'Лес', 'Озеро', 'Овраг', 'Обнажение', 'Лесной', 'Дуб', 'Группа', 'Гора', 'Санаторий']
    names = [item for item in names if item not in stop_list]
    addr = ', '.join(names)

    # region + district
    addr = (elems[8].split(' + '))[0]+', '+(elems[9].split(' + '))[0] + ', ' + addr

    return yandex_geolocate(addr)


def get_coords_from_description(descr):

    descr = descr.replace('с.ш. и', 'с.ш.')
    descr = descr.replace(' ', '')
    descr = descr.replace('(0)', '°')
    descr = descr.replace("'СШ", "'с.ш.")
    descr = descr.replace("'ВД", "'в.д.")
    descr = descr.replace('º', '°')
    descr = descr.replace('\(\)', '')
    descr = descr.replace("''", "\"")
    descr = descr.replace("´´", "\"")
    descr = descr.replace("'‘", "\"")
    descr = descr.replace(',', '.')
    descr = descr.replace(';', '')
    descr = descr.replace('..', '.')

    # 52°54'32,97'' с.ш., 47°38'28,18'' в.д.
    coords1 = re.findall('(\d+)°(\d+)[´′ʼ‘’\']([\d\.]+)[″”\"]с\.ш\.(\d+)°(\d+)[´′ʼ‘’\']([\d\.]+)[″”\"]в\.д\.', descr, re.UNICODE)

    # 52°54' с.ш., 47°38' в.д.
    coords2 = re.findall('(\d+)°([\d\.]+)[´′ʼ‘’\'″”\"]с\.ш\.(\d+)°([\d\.]+)[´′ʼ‘’\'″”\"]в\.д\.', descr, re.UNICODE)

    # 34,40167° с.ш.; 52,73472° в.д.
    coords3 = re.findall('\.?([\d\.]+)°?с\.ш\.([\d\.]+)°?в\.д\.', descr, re.UNICODE)

    # 34,40167° в.д., 52,73472° с.ш.
    coords4 = re.findall('\.?([\d\.]+)°?в\.д\.([\d\.]+)°?с\.ш\.', descr, re.UNICODE)
    if len(coords4)>0:
        # swap lat and lon
        temp_coords=[]
        for i in coords4:
            i=list(i)
            temp_coords.append(tuple([i[1], i[0]]))
        coords4=temp_coords

    coords=coords1+coords2+coords3+coords4

    lats=[]
    lons=[]
    for c in coords:
        if len(c)==6:
            p = geopy.point.Point(c[0]+' '+c[1]+'m '+c[2]+'s N '+c[3]+' '+c[4]+'m '+c[5]+'s E')
            lats.append(p.latitude)
            lons.append(p.longitude)
        elif len(c)==4:
            p = geopy.point.Point(c[0]+' '+c[1]+'m N '+c[2]+' '+c[3]+'m E')
            lats.append(p.latitude)
            lons.append(p.longitude)
        elif len(c)==2:
            p = geopy.point.Point(c[0]+' N '+c[1]+' E')
            lats.append(p.latitude)
            lons.append(p.longitude)

    if len(lats)>0:
        return(str(sum(lats) / float(len(lats)))+', '+str(sum(lons) / float(len(lons))))
    else:
        return('')


def add_coords():
    with open('oopt.csv', 'r', encoding='utf-8') as csv:
        lines = csv.read()

    lines = lines.splitlines()

    out = open('oopt_with_coords.csv', 'w', encoding='utf-8')
    for line in lines:
        if 'Название^Текущий статус ООПТ^' in line:
            out.write('DescrCoords^YandexGeolocateCoords^'+line+'\n')
        else:
            r = get_coords_from_description(line)+'^'+geolocate_by_description(line)+'^'
            print(line[:30], r)
            out.write(r+line+'\n')
    out.close()




get_list()
get_pages()
parse_pages()
add_coords()