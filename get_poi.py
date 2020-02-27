#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: baoyi
# Datetime: 2020/2/14 13:15

import requests
import configparser
import sqlite3
import argparse
from tqdm import tqdm
from pypinyin import lazy_pinyin as pinyin

gaode_key = '在这里输入你的高德key'

# 读取配置
cf = configparser.ConfigParser()
cf.read("ConfigParser.conf")

# 配置sqlite
conn = sqlite3.connect('gaode.sqlite', check_same_thread=False)
# 获取游标
cursor = conn.cursor()


def get_city_bound(city: str):
    """
    获取待爬取城市的边界值
    :param city
    :return:
    """

    # 如果city 在配置文件中存在，则pass，否则写入
    city_pinyin_config = ''.join(pinyin(city))

    if city_pinyin_config in cf.sections():
        print(city + '配置文件已存在')
        pass
    else:
        url = f'https://restapi.amap.com/v3/config/district?keywords={city}&subdistrict=1&extensions=all&key={gaode_key}'
        polyline = requests.get(url).json()['districts'][0]['polyline'].replace('|', ';').split(';')

        lng_list = []
        lat_list = []
        for point in polyline:
            lng = point.split(',')[0]
            lat = point.split(',')[1]
            lng_list.append(float(lng))
            lat_list.append(float(lat))

        min_lat = min(lat_list)
        min_lng = min(lng_list)
        max_lat = max(lat_list)
        max_lng = max(lng_list)

        # 写入config
        cf.add_section(city_pinyin_config)
        cf.set(city_pinyin_config, 'name', city_pinyin_config)
        cf.set(city_pinyin_config, 'start_lat', str(min_lat))
        cf.set(city_pinyin_config, 'end_lat', str(max_lat))
        cf.set(city_pinyin_config, 'start_lng', str(min_lng))
        cf.set(city_pinyin_config, 'end_lng', str(max_lng))

        with open('ConfigParser.conf', 'w+') as f:
            cf.write(f)

        print(city + ' 信息写入配置文件成功')


class CrawlPOI:
    """
    抓取poi
    """

    def __init__(self, city, radius):
        # 抓取的城市
        self.city = ''.join(pinyin(city))
        # POI抓取半径
        self.radius = radius

        # 每秒代表的米数
        self.LAT_SEC = 30.9
        self.LNG_SEC = 23.6
        # 获取并写入边界
        get_city_bound(city)

        # 创建数据库
        cursor.execute(f"""
                    create table if not exists {self.city}_poi(
                	id varchar(50) not null
                		primary key,
                	name text null,
                	type varchar(100)null,
                	typecode varchar(50) null,
                	lng double null,
                        lat double null,
                	distance varchar(5) null);""")

        conn.commit()

    def get_poi_nearby(self, location):
        """
        根据高德api获取数据
        :param location:
        :return:
        """
        page = 1
        while True:
            url = f'https://restapi.amap.com/v3/place/around?key={gaode_key}&location={location}&types' \
                  f'=050000|110000|200000|170000|060000|150000|160000|140000|120000|070000' \
                  f'|080000|090000|130000|100000|010000|030000|020000&radius={self.radius}&offset=20&page=' \
                  f'{page}&extensions=base'
            j = requests.get(url, timeout=(5, 5)).json()
            if int(j['count']) > 1000:
                print("数量超过1000 " + str(j['count']) + " 如果数据较多请减小radius的值")
            if j['pois']:
                pois = j['pois']
                data = []
                sql = "INSERT OR IGNORE INTO {city}_poi(id, name, type, typecode, lng, lat, distance) VALUES {data}"
                for poi in pois:
                    poi_id = poi['id']
                    poi_name = poi['name']
                    poi_type = poi['type']
                    poi_typecode = poi['typecode']
                    poi_lng, poi_lat = list(map(float, poi['location'].split(',')))
                    poi_distance = poi['distance']
                    tup = (poi_id, poi_name, poi_type, poi_typecode, poi_lng, poi_lat, poi_distance)
                    data.append(str(tup))

                cursor.execute(sql.format(city=self.city, data=','.join(data)))
                conn.commit()
                page += 1

            else:
                break

    def allocate_locations(self):
        """
        分配位置
        :return:
        """
        # 获取城市经纬度
        start_lat = cf.getfloat(f"{self.city}", "start_lat")
        start_lng = cf.getfloat(f"{self.city}", "start_lng")
        end_lat = cf.getfloat(f"{self.city}", "end_lat")
        end_lng = cf.getfloat(f"{self.city}", "end_lng")

        step_lng = (self.radius / self.LNG_SEC) / 3600
        step_lat = (self.radius / self.LAT_SEC) / 3600

        # 将参数读入列表准备多线程计算
        lat_list = []
        lng_list = []
        read_list = []

        for j in range(int((end_lng - start_lng) * 3600 * self.LNG_SEC / self.radius)):
            position_lng = round(float(start_lng + step_lng * j), 6)
            lng_list.append(position_lng)

        for j in range(int((end_lat - start_lat) * 3600 * self.LAT_SEC / self.radius)):
            position_lat = round(float(start_lat + step_lat * j), 6)
            lat_list.append(position_lat)

        try:
            with open('read.txt', 'r') as f:
                for i in f.readlines():
                    read_list.append(round(float(i.strip('\n')), 6))
        except Exception as e:
            pass

        # 删除重复的lat
        final_lat = []
        for i in lat_list:
            if i in read_list:
                pass
            else:
                final_lat.append(i)

        for lat in tqdm(final_lat, desc="1st loop"):
            for lng in tqdm(lng_list, desc="2nd loop"):
                location = str(lng) + "," + str(lat)
                try:
                    self.get_poi_nearby(location)
                except Exception as e:
                    print(e)
                    continue

            with open('read.txt', 'a') as f:
                f.write(str(lat) + '\n')


if __name__ == '__main__':
    parse = argparse.ArgumentParser()
    parse.add_argument('--city', type=str, default='北京', help='待抓取的城市')
    parse.add_argument('--radius', type=int, default=500, help='POI搜索半径' )

    args = parse.parse_args()
    city = args.city
    radius = args.radius

    # 开始抓取数据
    crawl = CrawlPOI(city, radius)
    crawl.allocate_locations()
