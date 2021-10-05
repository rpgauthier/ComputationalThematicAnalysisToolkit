# Computational Thematic Analysis Toolkit

## Installation Instructions

To Access most resent version 0.8.1: 

Installers avaliable for Windows 10 x64 and OSX 

## To Modify or Build using pip on windows or equalivilent on OSX
Download or Fork repository
Open src folder in an IDE (tested in VS Code)

### Build Commands
#### Windows:
1) pyinstaller pyinstaller-Windows10x64.spec --additional-hooks-dir=.'
2) innosetup_Windows10x64.iss
#### OSX:
<TBD>

### Needed applications
python 3.9
Inno Setup Compiler

### Needed Packages
- pip install psutil
- pip install wxPython
- pip install pandas
- pip install gensim
- pip install bitermplus
- pip install spacy
- pip install nltk
- pip install tweepy
- pip install chardet
- pip install dateparser
- pip install jsonpickle
- pip install wordcloud
- pip install squarify
- pip install networkx
- pip install pyinstaller

### Additional Steps
- python -m spacy download fr_core_news_sm
- python -m spacy download en_core_web_sm
