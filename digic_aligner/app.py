import sys
import flask
import os
from flask import jsonify, url_for
import yaml
import requests
from digic_aligner import doc
from digic_aligner.variables import METHOD, THRESHOLD
import html
import itertools
import datetime

app = flask.Flask(__name__)

from flaskext.markdown import Markdown
Markdown(app)
app.config['DEBUGING'] = True
app.config['TEMPLATES_AUTO_RELOAD']=True
app.config['CODEDIR']=os.getenv("DIGIC_CODEHOME", "/home/ginter/digicampus-aligner")

#METHOD=os.getenv("METHOD", "tfidf")
#THRESHOLD=float(os.getenv("THRESHOLD", "1.5"))
vectorizer=None
if METHOD=="tfidf":
    # Results on the tilinpäätös data not good, turn off
    #import pickle
    #with open("Data/vectorizer.pickle",'rb') as f:
    #    vectorizer=pickle.load(f)
    pass

doc_collections={}
search_results={}

@app.route("/docs")
def help():
    return flask.render_template("md.html",md=open("api_doc.md").read(),title="API docs"), 200

@app.route("/")
def index_page():
    return flask.render_template("index.html")

@app.route("/get_search_results/<doc_collection_id>",methods=['GET'])
def get_search_results(doc_collection_id):
    global search_results
    try:
        result=search_results[doc_collection_id]
        return jsonify({"search_results":result})
    except KeyError:
        return "Unknown query",400

@app.route("/get_doc_similarity_matrix/<doc_collection_id>",methods=['GET'])
def get_doc_similarity_matrix(doc_collection_id):
    global doc_collections
    doc_collection=doc_collections.get(doc_collection_id)
    if doc_collection is None:
        return "Unknown collection", 400
    M=doc_collection.doc_doc_sim_matrix_tfids_margin.tolist()
    doc_ids=doc_collection.get_doc_ids()
    return jsonify({"doc_ids":doc_ids,"M":M})

    

@app.route("/upload_docs",methods=['POST'])
def upload():
    global doc_collections, vectorizer
    doc_collection_id=datetime.datetime.now().isoformat()
    uploaded_file=flask.request.files.get('file')
    yaml_data=uploaded_file.read().decode("utf-8")
    data=yaml.load(yaml_data)

    # If the uploaded file is not in the correct format, this is where it breaks
    try:
        doc_collection=doc.DocCollection(data,vectorizer=vectorizer)
    except TypeError:
        return "",400
    doc_collections[doc_collection_id]=doc_collection
    indexed_docs=doc_collection.get_doc_ids()
    print("Indexed:",indexed_docs)
    return jsonify({"indexed_documents":indexed_docs,"doc_collection_id":doc_collection_id}),200

def get_template_data(result):
    """
    {'qry_segmentation': {'segmented': ['keiju']}, 'hits': [{'target_id': 'd1', 'target_segmentation': {'segmented': ['Olen pieni keiju ja leijailen metsän reunoissa .', 'Tykkään tavata uusia ihmisiä .', 'Erityisesti sienestäjät ovat minulle mieluisia .', 'Kermassa .', 'Ha haaa .', 'Sienet on minun !', 'Ei niitä saa minulta ottaa pois .']}, 'matching_segments': [(0, 0, 5.44709292036094)], 'avg_match': 5.44709292036094}, {'target_id': 'd2', 'target_segmentation': {'segmented': ['Metsässä asuu keijut .', 'Ne on pieniä mutta todella vihaisia .', 'Ne tappaa sienestäjiä ja paistaa ne .', 'Kermassa .', 'Hyi .']}, 'matching_segments': [(0, 0, 4.038449243631546)], 'avg_match': 4.038449243631546}, {'target_id': 'd0', 'target_segmentation': {'segmented': ['Kylläpä olen iloinen pikkulintu !', 'Elämä maistuu ja taivas on sininen .', 'Kesä on tulossa .', 'Onhan minun elämäni kaunista .', 'Tsirp fucking tsirp !']}, 'matching_segments': [(0, 2, 2.7152629749459716)], 'avg_match': 2.7152629749459716}]}
    """

    template_data=[]

    highlight_data={} #id of what is clicked -> [ids of what is highlighted]
    
    qry_segments=result["qry_segmentation"]["segmented"] #this is pretty much what we get from the query_tfidf
    for docidx,hit in enumerate(result["hits"]):

        hit_template_data=[] #list of (qsentence,qcolor,tsentence,tcolor) used to fill the result template
        hit_template_data_dict = {"docid": hit["target_id"]} # {"docid": docid, "hit_segments": hit_template_data}

        hit_segments=hit["target_segmentation"]["segmented"]
        #TODO: can this be made somehow ... better?
        #hit["matching_segments"] sequence of (q_idx,tgt_idx,margin)
        for q_idx,tgt_idx,margin in hit["matching_segments"]:
            q_span=f"span_qry_{docidx}_{q_idx}"
            t_span=f"span_target_{docidx}_{tgt_idx}"
            highlight_data.setdefault(q_span,[]).append(t_span)
            highlight_data.setdefault(t_span,[]).append(q_span)
        matching_qry=set(match[0] for match in hit["matching_segments"]) #these match in qry
        matching_tgt=set(match[1] for match in hit["matching_segments"]) #these match in target
        for i,(qry,tgt) in enumerate(itertools.zip_longest(qry_segments,hit_segments,fillvalue="")):
            if i in matching_qry:
                qclass="match"
            else:
                qclass="nonmatch"
            
            if i in matching_tgt:
                tclass="match"
            else:
                tclass="nonmatch"
            
            hit_template_data.append((docidx,i,qry,qclass,tgt,tclass))
        hit_template_data_dict["hit_segments"] = hit_template_data
        template_data.append(hit_template_data_dict)
    print("HIGHLIGHT DATA",highlight_data)
    return template_data,highlight_data

@app.route("/qry_by_id/<doc_collection_id>/<docid>",methods=['GET'])
def qry_by_id(doc_collection_id,docid):
    global doc_collections, THRESHOLD, search_results
    doc_collection=doc_collections.get(doc_collection_id)
    if doc_collection is None:
        return "Unknown collection", 400
    result=doc_collection.query_by_doc_id(docid,method=METHOD,margin_cutoff=THRESHOLD)
    query_id=doc_collection_id+docid
    search_results[query_id]=result
    print("RESULT:\n",result, file=sys.stderr)
    template_data,highlight_data=get_template_data(result)
    rendered=flask.render_template("result_templ.html",resultdata=template_data)
    print("Queried collection",doc_collection_id,file=sys.stderr)
    #print("HIGHLIGHT_DATA:", highlight_data)
    return jsonify({"result_html":rendered,"highlight_data":highlight_data,"query_id":query_id}),200

@app.route("/qrytxt/<doc_collection_id>",methods=['POST'])
def qry_text(doc_collection_id):
    global doc_collections, THRESHOLD, search_results
    doc_collection=doc_collections.get(doc_collection_id)
    if doc_collection is None:
        return "Unknown collection", 400
    text=flask.request.form["text"]
    if not text.strip():
        return "No input text as query", 400
    
    print("TEXT=",text)
    print(doc_collection)
    result=doc_collection.query(text,method=METHOD,margin_cutoff=THRESHOLD)
    query_id=doc_collection_id
    search_results[query_id]=result
    template_data,highlight_data=get_template_data(result)
    rendered=flask.render_template("result_templ.html",resultdata=template_data)
    print("RETURNING",rendered)
    #print('HIGHLIGHT_DATA', highlight_data)
    print("Queried collection",doc_collection_id,file=sys.stderr)
    return jsonify({"result_html":rendered,"highlight_data":highlight_data,"query_id":query_id}),200

