# Gaodo_POI
利用api抓取城市的高德poi数据，方便简洁。持续更新分享数据。

### Introduction

填入Key以后只需要两个参数即可抓取一个城市中的POI数据，并且存入sqlite中

### How to use

```bash
python get_poi.py --city <填入待抓取程序> --radius <填入搜索半径(m)>
```

例如
```bash
python get_poi.py --city 北京 --radius 500
```

如果一切正常会在当前文件夹生成三个文件，**ConfigParser.conf、 gaode.sqlite、read.txt**

1. **ConfigParser.conf**
是自动生成的程序的配置文件，保存了城市的经纬度范围。可以自己手动更改获取更大或者更小的范围。

2. **gaode.sqlite**
是一个sqlite数据库，保存着poi的数据。

3. **read.txt**
保存着已经抓取过得经纬度范围，便于断点续抓

### Data Description

数据一共有 **id, name, type, typecode, lng, lat, distance** 7个字段。示例如下

| id| name | type | typecode | lng | lat | distance |
| :------: | :----: | :----: | :------: | :------: | :------: | :------: |
| B02E20O06Z | 株木山站 | 交通设施服务;火车站;火车站 |150200|111.890042644959|27.851164|96|
| B0FFLCC8YV | 矿区医院 | 医疗保健服务;综合医院;综合医院 |090100|111.889904|27.853122|198|


### Data Share
数据分析。如果你不想抓取数据, 我手里有一些现成的数据，可以发邮件联系我获取。
