import csv
import json
from collections import defaultdict, Counter
from flask import Flask, render_template, jsonify

app = Flask(__name__)

CSV_FILE = r'data\analysis_results.csv'

def load_creator_sponsor_graph():
    nodes = {}
    links = []
    creator_sponsor_count = Counter()
    sponsor_creators = defaultdict(set)

    with open(CSV_FILE, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            creator = row['Creator Name'].strip()
            sponsor = row['Sponsor Name'].strip()
            if not creator or not sponsor or sponsor.lower() == "no sponsor":
                continue
            creator_id = f'creator_{creator}'
            sponsor_id = f'sponsor_{sponsor}'
            nodes[creator_id] = {"id": creator_id, "name": creator, "type": "creator"}
            nodes[sponsor_id] = {"id": sponsor_id, "name": sponsor, "type": "sponsor"}
            links.append({"source": creator_id, "target": sponsor_id})
            creator_sponsor_count[(creator, sponsor)] += 1
            sponsor_creators[sponsor].add(creator)

    # Find the (creator, sponsor) pair with the maximum collaborations
    if creator_sponsor_count:
        max_pair = max(creator_sponsor_count, key=creator_sponsor_count.get)
    else:
        max_pair = None

    # Mark the max pair in the links
    for link in links:
        c_name = nodes[link["source"]]["name"]
        s_name = nodes[link["target"]]["name"]
        link["highlight"] = (max_pair is not None and (c_name, s_name) == max_pair)

    return {
        "nodes": list(nodes.values()),
        "links": links,
        "max_pair": max_pair
    }

def load_industry_graph():
    nodes = {}
    links = []
    industry_count = Counter()

    with open(CSV_FILE, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            c_ind = row['Creator Industry'].strip()
            s_ind = row['Sponsor Industry'].strip()
            if not c_ind or not s_ind or s_ind.lower() == "n/a":
                continue
            c_id = f'creator_ind_{c_ind}'
            s_id = f'sponsor_ind_{s_ind}'
            nodes[c_id] = {"id": c_id, "name": c_ind, "type": "creator_industry"}
            nodes[s_id] = {"id": s_id, "name": s_ind, "type": "sponsor_industry"}
            links.append({"source": c_id, "target": s_id})
            industry_count[(c_ind, s_ind)] += 1

    # Find the (creator_industry, sponsor_industry) pair with the maximum collaborations
    if industry_count:
        max_pair = max(industry_count, key=industry_count.get)
    else:
        max_pair = None

    # Mark the max pair in the links
    for link in links:
        c_name = nodes[link["source"]]["name"]
        s_name = nodes[link["target"]]["name"]
        link["highlight"] = (max_pair is not None and (c_name, s_name) == max_pair)

    return {
        "nodes": list(nodes.values()),
        "links": links,
        "max_pair": max_pair
    }


