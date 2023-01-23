import textwrap

import requests
import xml.etree.ElementTree as ET
import json
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network

if __name__ == '__main__':
    bvid = 'BV1824y1r7mK'
    bvid = 'BV18m4y1F7wb'
    node2title = {}
    nodelist = set()
    edgelist = set()

    # First step: Judge the video is an interactive video or not
    r = requests.get('https://api.bilibili.com/x/player.so?id=cid:1&bvid=' + bvid)
    if r.status_code != 200:
        print('error: cannot get graph_version')
        exit(-1)
    eletent_tree = ET.fromstring('<root>' + r.text + '</root>')
    interaction = eletent_tree.find('interaction').text
    if interaction is None:
        print('error: video is not interactive')
        exit(-1)

    # Second step: Get the graph_version and get root node
    queue = []
    vis = []
    graph_version = str(json.loads(interaction)['graph_version'])
    #print(graph_version)
    r = requests.get('https://api.bilibili.com/x/stein/nodeinfo?bvid=' + bvid + '&graph_version=' + graph_version)
    if r.status_code != 200:
        print('error: cannot get node info')
        exit(-1)
    req = json.loads(r.text)
    #print(r.text)
    if req['code'] != 0:
        print('error: cannot get node info')
        exit(-1)
    root_id = req['data']['node_id']
    node2title[root_id] = req['data']['title']
    nodelist.add(root_id)
    vis.append(root_id)
    for node in req['data']['story_list']:
        node2title[node['node_id']] = node['title']
        nodelist.add(node['node_id'])
        queue.append(node['node_id'])
    for edge in req['data']['edges']['choices']:
        edgelist.add((root_id, edge['node_id'], textwrap.fill(edge['option'], width=10)))
        nodelist.add(edge['node_id'])
        queue.append(edge['node_id'])
    print(queue)

    # Third step: Loop and get the rest of the nodes
    while len(queue) > 0:
        node_id = queue.pop(0)
        if node_id in vis:
            continue
        vis.append(node_id)
        r = requests.get('https://api.bilibili.com/x/stein/nodeinfo?bvid=' + bvid + '&graph_version=' + str(graph_version) + '&node_id=' + str(node_id))
        if r.status_code != 200:
            print('error: cannot get node info')
            exit(-1)
        req = json.loads(r.text)
        if req['code'] != 0:
            print('error: cannot get node info')
            exit(-1)
        node2title[node_id] = req['data']['title']
        for node in req['data']['story_list']:
            node2title[node['node_id']] = node['title']
            nodelist.add(node['node_id'])
            queue.append(node['node_id'])
        if 'edges' not in req['data']:
            continue
        for edge in req['data']['edges']['choices']:
            edgelist.add((node_id, edge['node_id'], textwrap.fill(edge['option'], width=10)))
            nodelist.add(edge['node_id'])
            queue.append(edge['node_id'])
        print(vis)

    # Fourth step: Draw the graph
    plt.figure(figsize=(30, 30), dpi=200)
    G = nx.DiGraph()
    for node in nodelist:
        G.add_node(node, label=node2title[node].replace(' ',''))
    for (u, v, w) in edgelist:
        G.add_edge(u, v, label=w)
    pos = nx.spring_layout(G, k=1, iterations=300)
    nx.draw(G, pos, font_family='SimSun')
    node_labels = nx.get_node_attributes(G, 'label')
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_family='SimSun')
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_family='SimSun')
    plt.show()

    nt = Network('750px', '1440px')
    # populates the nodes and edges data structures
    nt.from_nx(G)
    nt.show('nx.html')
