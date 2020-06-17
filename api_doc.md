# Documentation

The DigiCampus essay evaluation prototype identifies similarly written student essays and the parts that contribute to the similarity.


## Quick start

Launch the API from terminal with the command `./run_flask.sh`. In the browser, access the corresponding port on localhost. Upload a set of documents in yaml format and query.


## Environmental variables for launching the API

The environmental variables can be set in the `run_flask.sh` script.

### The port used by udpipe `PORT`

Udpipe is used to preprocess essays and a single-threaded server process for it is started in the script `run_flask.sh`. Defaults to 6000.


### Setting the algorithm to be used `METHOD`

Choose the underlying algorithm for text content identification.

optional, defaults to `tfidf`

Possible values: {`tfidf`, `laser`, `bert`}, `laser` and `bert` require a GPU. `laser` is recommended when there is access to a GPU.


### Setting the cutoff for sentence similarity `THRESHOLD`

Sets the threshold at which a sentence is returned as a match for another. The higher the threshold, the more similar a candidate has to be to the query to be a match.

optional, defaults to `1.7` for `tfidf`, `1.1` for `laser`, and `1.07` for `bert`


## API reference

### Upload documents `upload`

Uploads the essays in yaml format. The essays to be processed together are to be uploaded as a single yaml file. The yaml file is a list of dictionary, where an item in the dictionary is a document (essay). There are two mandatory keys for a dictionary: `id` as the id of the document, and `text` for the content of the document.

- Endpoints:
    - POST `/upload_docs`
- Parameters:
    - None
- Returns:
    - a json object containing
        - `indexed_documents`: ids of the documents in the collection
        - `doc_collection_id`: id assigned for the uploaded collection


### Get document similarity matrix for a set of documents `get_doc_similarity_matrix`

Exposes the document similarity matrix as json.

- Endpoints:
    - GET `/get_doc_similarity_matrix/<doc_collection_id>`
- Parameters:
    - doc_collection_id, required:
        - string, document collection id `doc_collection_id` returned by `upload`
- Returns:
    - a json object containing
        - `doc_ids`: list of all the ids of the uploaded collection
        - `M`: similarity matrix of the uploaded collection


### Get search results `get_search_results`

Exposes search results from document or text query as json.

- Endpoints:
    - GET `/get_search_results/<query_id>`
- Parameters:
    - query_id, required:
        - string returned by qry_by_id or qry_text
- Returns:
    - a search result json object containing
        - `hits`: a list of retrieved documents
            - `avg_match`: the average of the similarity scores of all matching segments
            - `matching segments`: list of tuples with three elements
                - first element: the sentence index of the matching sentence from the query document
                - second element: the sentence index of the matching sentence from the retrieved document
                - third element: the similarity score between these two sentences
            - `target_id`: id of the matching document
            - `target_segmentation`: the retrieved document segmented into sentences
        - `qry_segmentation`: the query text segmented into sentences


### Query by document `qry_by_id`

Query by a document from a collection. Searches for similar essays in the collection.

- Endpoints:
    - GET `/qry_by_id/<doc_collection_id>/<docid>`
- Parameters:
    - doc_collection_id, required:
        - string, document collection id `doc_collection_id` returned by `upload`
    - docid, required:
        - string, document id returned by `upload`
- Returns:
    - a json object containing
        - `result_html`: result of the search in html
        - `highlight_data`: dictionary where the key is the sentence id of a sentence that can be highlighted, and the value is a list of sentences to be highlighted for a given sentence
        - `query_id`: id assigned for a particular query


### Query by text `qry_text`

Query by text. The text can range from a single sentence to an essay. The input text is processed as a document (an essay). Searches for similar essays in the collection.

- Endpoints:
    - POST `/qrytxt/<doc_collection_id>`
- Parameters:
    - doc_collection_id, required:
        - string, document collection id `doc_collection_id` returned by `upload`
- Returns:
    - a json object containing
        - `result_html`: result of the search in html
        - `highlight_data`: dictionary where the key is the sentence id of a sentence that can be highlighted, and the value is a list of sentences to be highlighted for a given sentence
        - `query_id`: id assigned for a particular query


## Errors

### Uploaded file format incorrect. Please refer to the documentation for the required format.

The essays to be processed together are to be uploaded as a single yaml file. The yaml file is a list of dictionary, where an item in the dictionary is a document (essay). There are two mandatory keys for a dictionary: `id` as the id of the document, and `text` for the content of the document.

Example yaml file:

```
- id: d0
  text: "This is a fake student essay. The document id can be any strings as long as there is no duplicate."
- id: d1
  text: "This is another fake student essay. An essay has multiple sentences. Let's make it three."
```


### No input text as query

No text in the box for text query. The `text query` button is not intended for document query.


### No matching results

No document with similarity scores exceeding the threshold was found. Please lower the threshold.


### Unknown collection

The document collection id specified was not found.


### Unknown query

The query id was not found.