#!/usr/bin/env python3
import json
import sys
import os
import zipfile
import random
from urllib.request import urlopen


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

tasks = {}
rnd = []
with open('tasks.txt', 'r') as f:
    mapbbcode = next(f).strip()
    for line in f:
        p = line.find(' ')
        if p > 0:
            rnd.append(line[p+1:].strip())
            if p > 3:
                tasks[line[:p]] = line[p+1:].strip()

with urlopen('http://share.mapbbcode.org/{}?format=geojson'.format(mapbbcode)) as resp:
    if resp.getcode() != 200:
        print('Error requesting a geojson: {}'.format(resp.getcode()))
        sys.exit(2)
    data = json.load(resp)['features']

images = {x[:x.find('.')]: x for x in os.listdir('.') if x.endswith('.jpg')}
images = {'5881': '5881.jpg'}

marks = {}
for f in data:
    coords = f['geometry']['coordinates']
    title = f['properties'].get('title')
    if not title:
        code = str(random.randint(1000, 9999))
    elif title[0] == 's':
        code = title[1:]
    else:
        code = title

    if code in tasks:
        desc = tasks[code]
    else:
        desc = random.choice(rnd)

    if code in images:
        img = images[code]
    else:
        img = random.choice(list(images.values()))
    desc += '<br><br><img src="http://osmz.ru/mapsme7/{}" width="320">'.format(img)

    marks[code] = '''
  <Placemark>
    <name>{code}</name>
    <styleUrl>#placemark-purple</styleUrl>
    <description>{desc}</description>
    <Point><coordinates>{lon},{lat}</coordinates></Point>
  </Placemark>
    '''.format(code=code, desc=esc(desc), lon=coords[0], lat=coords[1])

kml = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://earth.google.com/kml/2.2">
<Document>
  <Style id="placemark-purple">
      <IconStyle>
          <Icon>
              <href>http://mapswith.me/placemarks/placemark-purple.png</href>
          </Icon>
      </IconStyle>
  </Style>
  <name>Семилетие MAPS.ME</name>
  <visibility>1</visibility>
{}
</Document>
</kml>
'''.format('\n'.join([marks[code] for code in sorted(marks.keys(), reverse=True)]))

# with zipfile.ZipFile('mapsme7.kmz', 'w', zipfile.ZIP_DEFLATED) as z:
with zipfile.ZipFile('mapsme7.kmz', 'w') as z:
    with z.open('mapsme7.kml', 'w') as f:
        f.write(kml.encode('utf-8'))
