# Crawler
import requests
import re
import time
import json
import argparse
import numpy as np
from collections import deque
from lxml import html

def get_id_from_link(link):
    return int(link[48 :])

def shape_name(name, max_len = 20):
    name = re.sub(' +', ' ', name)
    if name[0] == ' ':
        name = name[1 :]
    if name[-1] == ' ':
        name = name[0 : -1]
    components = re.split(' ', name)
    lens = np.zeros(shape = (len(components)))
    for i in range(lens.shape[0]):
        lens[i] = len(components[i])
        if lens[i] > max_len:
            max_len = lens[i]
    shaped_name = ''
    cur = 0
    while cur < lens.shape[0]:
        shaped_name += components[cur]
        line_len = lens[cur]
        cur += 1;
        while cur < lens.shape[0] and line_len + lens[cur] + 1 <= max_len:
            shaped_name += ' ' + components[cur]
            line_len += lens[cur] + 1
            cur += 1
        if cur < lens.shape[0]:
            shaped_name += '\n'
    return shaped_name

arg_parser = argparse.ArgumentParser(description = '.')
arg_parser.add_argument('--crawl', action = 'store_false')
args = arg_parser.parse_args()
skip_crawling = args.crawl

# initialize
initial_id = 176358
link_prefix = 'https://genealogy.math.ndsu.nodak.edu/'
id_prefix = link_prefix + 'id.php?id='
initial_page = id_prefix + str(initial_id)

queue = deque()
queue.append(initial_page)
link_dict = {initial_id : {'advisors' : []}}

if not skip_crawling:
    # set max iter
    for i in range(200):
        delay = np.random.rand() * 0.5
        time.sleep(0.1 + delay)
        if len(queue) == 0:
            print('Queue is empty! You are not in majority genealogy!')
            break
        link = queue.popleft()
        page = requests.get(link)
        tree = html.fromstring(page.text)
        tree.make_links_absolute(link_prefix)
        paddingWrapper = tree.get_element_by_id('paddingWrapper')
        paddingWrapper_children = paddingWrapper.getchildren()

    # not sure this is correct
        name = paddingWrapper_children[2]
        name_str = name.text_content().replace('\n', '')
        print('Name: ', name_str)

    # store personal info
        id = get_id_from_link(link)
        link_dict[id]['name'] = name_str

    # locate advisor element
        found_advisors = False
        advisor_blocks = []
        for ele in paddingWrapper.iterchildren():
            if 'style' in ele.attrib and ele.attrib['style'] == 'text-align: center; line-height: 2.75ex':
                advisor_blocks.append(ele)
                found_advisors = True
            elif 'style' in ele.attrib and ele.attrib['style'] == 'text-align: center':
                content = ele.text_content()
                if 'Advisor' in content and 'Unknown' in content:
                    advisor_blocks.append(ele)
                    found_advisors = True
    
        if not found_advisors:
            raise AdvisorElementNotFound('')

    # get advisors' links
        for block in advisor_blocks:
            link_flag = True
            for ele in block:
                content = ele.text_content()
                if 'Advisor' in content and 'Unknown' in content:
                    print('Advisor: Unknown')
                    link_flag = not link_flag
                    continue
                if link_flag:
                    a_link = ele.attrib['href']
                    a_name = ele.text_content().replace('\n', '')
                    print('Advisor: ', a_name, '$Link: ', a_link)
                    a_id = get_id_from_link(a_link)
                    if a_id not in link_dict:
                        queue.append(a_link)
                        link_dict[a_id] = {'advisors' : []}
                    link_dict[id]['advisors'].append(a_id)
                link_flag = not link_flag
            print('\n')

    # backup
    original_link_dict = link_dict
    with open('backup.json', 'w') as f:
        json.dump(original_link_dict, f, indent = 4)

else:
# if skip crawling, read from backup
    with open('backup.json', 'r') as f:
        string_keyed_link_dict = json.load(f)
    for key, val in string_keyed_link_dict.items():
        link_dict[int(key)] = val

# fill the name field for unreached persons
for key, val in link_dict.items():
    if 'name' not in val:
        val['name'] = '...'

# Graph Construction
import networkx as nx
import matplotlib.pyplot as plot

graph = nx.DiGraph()
graph.add_nodes_from(list(link_dict.keys()))
for key, val in link_dict.items():
    graph.node[key] = {'name_': shape_name(val['name'], 18)}
    for advisor in val['advisors']:
        graph.add_edge(key, advisor)

pos = nx.nx_pydot.graphviz_layout(graph, 'dot')
labels = nx.get_node_attributes(graph, 'name_')
color = np.zeros(shape = (len(labels), 4))
color[:, 0] = 0.
color[:, 1] = .1
color[:, 2] = .9
color[:, 3] = .9
fig = plot.figure(figsize = (16.0, 16.0))
nx.draw_networkx(graph, pos = pos, with_labels = False, labels = None, alpha = 0.5, \
                 node_color = color, node_size = 60, node_shape = (4, 0, 0), linewidths = 1.0, \
                 width = 0.5, arrows = True, \
                 font_size = 6)
for key, val in pos.items():
    plot.annotate(s = labels[key], xy = (val[0] + 7, val[1]), fontsize = 6, va='center')
plot.axis('off')
#plot.show()
fig.savefig('image.png', dpi = 1000)