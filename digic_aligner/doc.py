import ufal.udpipe as udpipe
import sklearn.feature_extraction
import sklearn.metrics
import numpy
import sys
import yaml


class Doc:

    def __init__(self,doc_dict,udpipe_pipeline=None):
        self.doc_dict=doc_dict #this dictionary can have anything the user ever wants but must have "text" field and "id" field
        self.text=doc_dict["text"]
        self.id=doc_dict["id"]
        if udpipe_pipeline is not None:
            self.preproc_udpipe(udpipe_pipeline)

    def get_segmentation(self):
        #Tells the user how this document is segmented
        #TODO: modify this to tell character offsets rather than the actual sentences that have been destroyed by now by udpipe's tokenization
        #Whatever this returns should have enough information for the user to know what we mean when we say "segment index 5 is aligned with something"
        return {"segmented":self.lines_and_tokens}
        
            
    def preproc_udpipe(self,udpipe_pipeline):
        #This runs whatever preprocessing we need
        # Download UDPipe model from:
        # https://lindat.mff.cuni.cz/repository/xmlui/handle/11234/1-3131
        #
        # TODO: lemmatization/stemming/something would likely be quite useful for Finnish
        # TODO: store the result in some sort of Document object
        segmented=udpipe_pipeline.process(self.text)
        segmented=segmented.strip()
        self.lines_and_tokens=[line.strip() for line in segmented.split("\n") if line.strip()]
        #list of strings, each string is one whitespace-tokenized sentences, I don't split into tokens here on purpose
        #this is also a place to get lemmas and what have you

class DocCollection:

    def __init__(self,doc_dicts,udpipe_pipeline=None,vectorizer=None):
        self.udpipe_pipeline=udpipe_pipeline
        self.docs=[Doc(doc_dict,udpipe_pipeline) for doc_dict in doc_dicts]

        #1) Pre-compute the doc2doc sim matrix
        self.doc_doc_sim_matrix_tfidf,self.vectorizer=doc_sim_matrix_tfidf(self.docs,vectorizer) #if vectorizer is None, this function makes one, let's store it
        self.doc_doc_sim_matrix_tfids_margin=margin_doc_sim(self.doc_doc_sim_matrix_tfidf) #calculate also the margin-method based matrix (I dont think this has ever been done before!)

    def query_tfidf(self,text,margin_cutoff=2.0): #margin cutoff on sentences, anything below that is not considered
        """Given a query text, find hitting documents and align them. Prepares a dictionary which can be returned to the user"""
        qdoc=Doc({"text":text,"id":"qry"},udpipe_pipeline=self.udpipe_pipeline) #turn the query into a fake doc

        doc_hits=[] #this will be a list of the hits
        for d in self.docs: #and compare against all docs (I don't think we should use a doc-embedding approach here since queries will be short, so we really want the alignment)
            swise_sim=sentence_wise_sim_tfidf(qdoc,d,self.vectorizer)
            overlaps=overlapping_segments(swise_sim)
            segment_pairs=[]
            for qry_sent_idx,d_sent_idx,margin in zip(*overlaps): #here we have the actual alignments of query sentences with d's sentences
                if margin<margin_cutoff:
                    break
                segment_pairs.append((qry_sent_idx,d_sent_idx,margin)) #store these indices and margin so we can give them back to the user
            if len(segment_pairs)>0:
                doc_avg=sum(margin for i1,i2,margin in segment_pairs)/len(segment_pairs)
            else:
                continue #this one doesnt make the result
            doc_result={}
            doc_result["target_id"]=d.id
            doc_result["target_segmentation"]=d.get_segmentation()
            doc_result["matching_segments"]=segment_pairs
            doc_result["avg_match"]=doc_avg
            doc_hits.append(doc_result)
        doc_hits.sort(key=lambda dhit:dhit["avg_match"],reverse=True) #sort so that best docs come first

        #now yet give some sort of info about the query
        result={"qry_segmentation":qdoc.get_segmentation(),"hits":doc_hits} #this can basically be returned as a json
        return result


####### HERE's then the generic function for sim calc etc
        
# I don't think this needs a BERT version
# all the docs will be similar to each other, so I think individual words matter
# so maybe tfidf is just fine
# Returs doc x doc similarity matrix
def doc_sim_matrix_tfidf(segmented_docs,vectorizer=None):
    # segmented_docs is a list of Doc() that must have preproc_udpipe() ran on them in init
    # This is a document-by-document work, so we rejoin the sentences at least for the tfidf work
    docs_as_one_text=[" ".join(doc.lines_and_tokens) for doc in segmented_docs]
    if vectorizer is None: #TODO I really think we should have a vectorizer trained on a bunch of normal Finnish
        vectorizer=sklearn.feature_extraction.text.TfidfVectorizer(analyzer="char_wb",ngram_range=(2,5)) #TODO: should TF or IDF be somehow log-squeezed? This often helps. #TODO: rather give this a vectorizer from outside
        vectorizer.fit(docs_as_one_text)
    doc_by_term_M=vectorizer.transform(docs_as_one_text)
    doc_sim_matrix=sklearn.metrics.pairwise.cosine_similarity(doc_by_term_M)
    return doc_sim_matrix,vectorizer

def margin_doc_sim(doc_sim_matrix):
    # This takes any doc sim square matrix
    # and does the margin method on it
    M=doc_sim_matrix
    means12=M.mean(axis=-1)
    means21=M.T.mean(axis=-1)
    means=(means12+means21)/2.0
    #print("Means:",means)
    margins=M/means #This is again the margin method, bidirectional, and done on documents
    margins=(margins+margins.T)/2 #make it symmetric yet by averaging the two triangles
    return margins
    


#TODO maybe someone could do a LASER version of this?
#TODO BERT version would be nice, but needs some effort to get the positions right and embedd the documents correctly
#TODO if we do Laser/BERT then probably these should be pre-embedded when reading the documents in, it doesnt matter for tfidf all that much, so that doesnt cache anything
def sentence_wise_sim_tfidf(d1_segm,d2_segm,vectorizer):
    """
    This gets two documents (one of these could be a query even)
    It runs a comparison of segments in d1 against segments in d2
    """
    #TODO: In future we could use some fancy machine translation aligner, but let's for now do the obvious
    #TODO: would using a vectorizer fitted on the current two documents, using a sentence as pseudo-document be a good idea?
    d1_vectorized=vectorizer.transform(d1_segm.lines_and_tokens) #sentence-by-term
    d2_vectorized=vectorizer.transform(d2_segm.lines_and_tokens) #sentence-by-term
    segment_wise_matrix=sklearn.metrics.pairwise.cosine_similarity(d1_vectorized,d2_vectorized,dense_output=True)
    #this is now d1 segments by d2 segments similarity matrix
    return segment_wise_matrix

# This takes the result of sentence_wise_sim() is agnostic to how that was done, right now we only have the tfidf version, but should work with anything
def overlapping_segments(segment_wise_matrix):
    M=segment_wise_matrix #just make this shorter in name
    #assumption: M is a similarity matrix of N1 x N2 elements, where N1 are segments from doc1 and N2 are segments from doc2
    #note: right now these are sentences, but I think whatever overlapping segments should be doable too
    # like phrases etc, so there is no deeply inbuilt assumption that these are sentences

    # the document lengths can differ considerably (especially if the other is a simple query)
    # I think it's good to compare all segments of the shorter doc against all segments of the longer doc and not the other way around
    d1_len,d2_len=M.shape
    if d1_len>d2_len:
        M=M.T

    #get the coefficients for the margin method
    #TODO: bidirectional margin, now only one-directional
    #https://arxiv.org/pdf/1811.01136
    sorted_M=-numpy.sort(-M,axis=-1) #funny how numpy sort does not have order parameter; this sorts target similarities (second dimension) for every source doc (first dimension)
    means_of_nearest=sorted_M[:,:10].mean(axis=-1)+0.00001  #10 neighbors seems a decent consensus, add a little epsilon not to divide by zero
    margin=sorted_M[:,0]/means_of_nearest #the sim of nearest doc divided by avg of sims of 10 nearest docs: the (c) method from the paper above
    targets=(-M).argsort(axis=-1)[:,0] #for every shorter document segment, this is the corresponding longer document segment 
    sources=numpy.arange(M.shape[0]) #indices into the shorter document basically (0,1,2,3....) so we can sort later
    
    #So now winner target segments and their margin are the results of the comparison, for each source segment
    best_sorting_indices=(-margin).argsort(axis=-1) #this sorts the hits from best to worst by margin
    final_sources=sources[best_sorting_indices] #indices into source
    final_targets=targets[best_sorting_indices] #indices into target
    final_margins=margin[best_sorting_indices]  #margins
    #the three above are now sorted from best-to-worst margin score
    if d1_len>d2_len: #undo the transpose
        return final_targets,final_sources,final_margins
    else:
        return final_sources,final_targets,final_margins

if __name__=="__main__":
    udpipe_model=udpipe.Model.load("Data/finnish-tdt-ud-2.5-191206.udpipe")
    udpipe_pipeline=udpipe.Pipeline(udpipe_model,"tokenize","none","none","horizontal") # horizontal: returns one sentence per line, with words separated by a single space
    docdicts=yaml.load(open("test_docs.yaml"))
    doc_collection=DocCollection(docdicts,udpipe_pipeline=udpipe_pipeline,vectorizer=None)
    
    # doc_src,doc_target=doc_collection.docs[1],doc_collection.docs[2]
    # M=sentence_wise_sim_tfidf(doc_src,doc_target,doc_collection.vectorizer)
    # for src_idx,target_idx,margin in zip(*overlapping_segments(M)):
    #     print(doc_src.lines_and_tokens[src_idx])
    #     print(doc_target.lines_and_tokens[target_idx])
    #     print(margin)
    #     print()
    r=doc_collection.query_tfidf("Keiju leijailee metsässä, erityisesti reunoissa. Se paistaa sienestäjät kermassa.",margin_cutoff=2.5)
    print(r)
    
    
