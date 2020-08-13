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

## Prepare data

The API takes in essays in the yaml format. A yaml file has all the essays that are to be compared in it. To generate the yaml file, run `python3 generate_yaml.py <dir_path>`, where `<dir_path>` is the directory containing the essays, each in a txt file. A yaml file is generated, which can be uploaded to the API.

## In the directory run 'run_flask.sh', go to the address in the browser

1) Load the yaml file

2) Once loaded (document ids will be populated in the dropdown) you can query by document or query by text

   Query by document: just pick one from the dropdown thats all

   Query by text: type in some query text, hit query


