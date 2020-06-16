# digicampus-aligner

# Install
```
cd Data
wget https://lindat.mff.cuni.cz/repository/xmlui/bitstream/handle/11234/1-3131/finnish-tdt-ud-2.5-191206.udpipe
cd ..

git clone https://github.com/ufal/udpipe.git
cd udpipe/src
make server
```

And then

```
pip install wheel
pip install -r requirements.txt
python3 -m laserembeddings download-models
```


# Run

In the directory run 'run_flask.sh', go to the address in the browser

1) Load the file test_docs.yaml

2) Once loaded (document ids will be populated in the dropdown) you can query by document or query by text

   Query by document: just pick one from the dropdown thats all

   Query by text: type in some query text, hit query


