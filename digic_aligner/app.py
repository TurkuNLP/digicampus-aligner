import flask
import os
from flask import jsonify, url_for
import yaml
import requests
from digic_aligner import doc
import ufal.udpipe as udpipe
import html
import itertools

app = flask.Flask(__name__)

from flaskext.markdown import Markdown
Markdown(app)
app.config['DEBUGING'] = True
app.config['TEMPLATES_AUTO_RELOAD']=True
app.config['CODEDIR']=os.getenv("DIGIC_CODEHOME", "/home/ginter/digicampus-aligner")



doc_collection=None

@app.route("/")
def index_page():
    return flask.render_template("index.html")

@app.route("/upload_docs",methods=['POST'])
def upload():
    global doc_collection
    uploaded_file=flask.request.files.get('file')
    yaml_data=uploaded_file.read().decode("utf-8")
    data=yaml.load(yaml_data)

    ### TODO: UDPIPE SEEMS SOMEHOW THREAD-UNSAFE
    ### I HAVE TO RELOAD IT HERE I DONT KNOW WHY
    ### TODO: Verify this!
    ### ...but right now this will do
    modelpath=os.path.join(app.config["CODEDIR"],"Data","finnish-tdt-ud-2.5-191206.udpipe")
    assert os.path.exists(modelpath)
    udpipe_model=udpipe.Model.load(modelpath)
    udpipe_pipeline=udpipe.Pipeline(udpipe_model,"tokenize","none","none","horizontal") # horizontal: ret
    
    doc_collection=doc.DocCollection(data,udpipe_pipeline=udpipe_pipeline)
    indexed_docs=doc_collection.get_doc_ids()
    print("Indexed:",indexed_docs)
    return jsonify({"indexed_documents":indexed_docs}),200

def get_template_data(result):
    """
{'qry_segmentation': {'segmented': ['keiju']}, 'hits': [{'target_id': 'd1', 'target_segmentation': {'segmented': ['Olen pieni keiju ja leijailen metsän reunoissa .', 'Tykkään tavata uusia ihmisiä .', 'Erityisesti sienestäjät ovat minulle mieluisia .', 'Kermassa .', 'Ha haaa .', 'Sienet on minun !', 'Ei niitä saa minulta ottaa pois .']}, 'matching_segments': [(0, 0, 5.44709292036094)], 'avg_match': 5.44709292036094}, {'target_id': 'd2', 'target_segmentation': {'segmented': ['Metsässä asuu keijut .', 'Ne on pieniä mutta todella vihaisia .', 'Ne tappaa sienestäjiä ja paistaa ne .', 'Kermassa .', 'Hyi .']}, 'matching_segments': [(0, 0, 4.038449243631546)], 'avg_match': 4.038449243631546}, {'target_id': 'd0', 'target_segmentation': {'segmented': ['Kylläpä olen iloinen pikkulintu !', 'Elämä maistuu ja taivas on sininen .', 'Kesä on tulossa .', 'Onhan minun elämäni kaunista .', 'Tsirp fucking tsirp !']}, 'matching_segments': [(0, 2, 2.7152629749459716)], 'avg_match': 2.7152629749459716}]}
    """

    template_data=[]
    
    qry_segments=result["qry_segmentation"]["segmented"] #this is pretty much what we get from the query_tfidf
    for hit in result["hits"]:

        # TODO: make this into a dictionary, store doc ids etc
        hit_template_data=[] #list of (qsentence,qcolor,tsentence,tcolor) used to fill the result template
        
        hit_segments=hit["target_segmentation"]["segmented"]
        #TODO: can this be made somehow ... better?
        matching_qry=set(match[0] for match in hit["matching_segments"]) #these match in qry
        matching_tgt=set(match[1] for match in hit["matching_segments"]) #these match in target
        for i,(qry,tgt) in enumerate(itertools.zip_longest(qry_segments,hit_segments,fillvalue="")):
            if i in matching_qry:
                qcolor="green"
            else:
                qcolor="black"
            
            if i in matching_tgt:
                tcolor="green"
            else:
                tcolor="black"
            
            hit_template_data.append((qry,qcolor,tgt,tcolor))
        template_data.append(hit_template_data)
    return template_data

@app.route("/qry_by_id/<docid>",methods=['GET'])
def qry_by_id(docid):
    global doc_collection
    result=doc_collection.query_by_doc_id(docid)
    template_data=get_template_data(result)
    rendered=flask.render_template("result_templ.html",resultdata=template_data)
    print("RETURNING",rendered)
    return jsonify({"result_html":rendered}),200

@app.route("/qrytxt",methods=['POST'])
def qry_text():
    global doc_collection
    text=flask.request.form["text"]
    if not text.strip():
        return jsonify({"result_html":""}),200 #TODO: I GUESS SOME ERROR SHOULD BE SHOWN
    
    ### TODO: UDPIPE SEEMS SOMEHOW THREAD-UNSAFE
    ### I HAVE TO RELOAD IT HERE I DONT KNOW WHY
    ### TODO: do something for gods sake!
    ### ...but right now this will have to do
    modelpath=os.path.join(app.config["CODEDIR"],"Data","finnish-tdt-ud-2.5-191206.udpipe")
    assert os.path.exists(modelpath)
    udpipe_model=udpipe.Model.load(modelpath)
    udpipe_pipeline=udpipe.Pipeline(udpipe_model,"tokenize","none","none","horizontal") # horizontal: ret
    doc_collection.udpipe_pipeline=udpipe_pipeline
    ### ^^^  THIS SUCKS!
    

    print("TEXT=",text)
    print(doc_collection)
    result=doc_collection.query_tfidf(text)
    template_data=get_template_data(result)
    rendered=flask.render_template("result_templ.html",resultdata=template_data)
    print("RETURNING",rendered)
    return jsonify({"result_html":rendered}),200

