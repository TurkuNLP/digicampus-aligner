# Documentation

The DigiCampus essay evaluation prototype identifies similarly written student essays and the parts that contribute to the similarity.

## Launching the API

The API is launched by running `./run_flask.sh` in the `digicampus-aligner` directory. In the `run_flask.sh`, two optional environmental variables can be defined to choose the underlying algorithm for text content identification.

`METHOD` can be `tfidf`, `laser`, or `bert`. The methods `laser` and `bert` require a GPU.

`THRESHOLD` sets the threshold at which a sentence is returned as a match for a another. The higher the threshold, the more similar a candidate has to be to the query to be a match.

If these two environmental variables are not set, the default values (`tfidf` with the threshold of `2.0`) is used. With a GPU, the recommended method would be `laser` with the default threshold of `1.1`.

After the launch in the terminal, the API can be accessed from the corresponding port on localhost.

## Upload essays

The essays to be processed together are to be uploaded as a single yaml file. The yaml file is a list of dictionary, where an item in the dictionary is a document (essay). There are two mandatory keys for a dictionary: `id` as the id of the document, and `text` for the content of the document.

To upload a yaml file, click browse and open the yaml file. A successfully loaded yaml file has its document similarity matrix exposed as json, which can be accessed by clicking the `Doc Similarity Matrix` link next to the text `Loaded collection`. This matrix records the similarity scores calculated for each pair of documents.

## Querying

There are two ways of querying: query by document, or query by text. Query by document uses a selected document as the query, and returns documents that are similar as calculated by the algorithm.

The preprocessing breaks any documents (essays or query text) into sentences. The returned results have automatically detected similar sentences in green. These green sentences can be clicked on by the cursor to have their corresponding similar sentences highlighted.

The search results are exposed as json, which can be accessed with the link `Search result` that appears after the search under the `Text query` button. The format of the json file is as follow: `search_results` contains `hits` and `qry_segmentation` (query segmentation). `hits` is a list, where each item is a retrieved document. `matching_segments` stores a list of tuples, where the first element in the tuple is the sentence index of the matching sentence from the query document, the second element is the sentence index of the matching sentence from the retrieved document, and the third element is the similarity score between these two sentences.

### Query by document

To query by document, select the document to be used as the query from the dropdown manual and wait for the calculation to finish. **Do not press the `Text query` button**, which is only intended for text query.

### Query by text

To query by text, input the text into the `Query by text` box and press the `Text qery` button. The input text is processed as a document would be. If there is no text in the box, an error message of `No input text as query` pops up.

If no document has similarity scores exceeding the threshold, the message `No matching results.` is returned.
