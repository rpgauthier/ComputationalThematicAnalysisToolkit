# Computational Thematic Analysis Toolkit

## Installation Instructions

To Access most recent version: https://github.com/rpgauthier/ComputationalThematicAnalysisToolkit/releases/latest

Installers available for Windows 10 x64 and OSX 

## Toolkit Functionality:
The Toolkit is made up of interconnected modules.

### Data Collection
Is used by the researcher to import data into the toolkit. Once imported the module visualizes the data's content so that the user can interact with the data at scale and become more familiar with the data and begin forming ideas about for their analysis. 

### Data Cleaning & Filtering
Provide the researcher the ability to: (1) see what rules are being used to include and remove words by the toolkit's internal application of computational techniques; (2) review which words are included and removed by the rules; and (3) to tune the rules to search for signals. During this process researchers can become more familiar with general dataset by seeing how different words are used by clicking on any word in the included or removed list. 

### Modelling & Sampling
Provides the ability for researcher to create a variety of purposive samples, using iterative topic models the seek to group data based on signals such as common word groupings in the comments, to provide a diverse set of models that capture samples of different sets of data. The researcher can use these samples to help them both further familiarize with the data as well as continue forming their inductive analytical framework.

### Coding
Provides the researcher with a place where data can be coded and reviewed in an iterative manner to develop, refine, and apply their analytical framework to sampled data in the form of a concrete set of codes.

### Reviewing
Provides the researcher a place to create themes, group codes within the themes and visualize connections between codes and themes.

### Reporting
Provides an interface to help the researcher choose quotes and keep track of which piece of data they came from for each code and theme and, if desired for ethical reasons, keep track of paraphrasing of these quotations to enable review with the research team about whether the paraphrase captured the original quotation properly.

## To Modify or Build a New version
Download or Fork repository
Open src folder in an IDE (tested in VS Code on Windows and OSX)

### Build Commands
#### Windows:
1) pyinstaller pyinstaller-Windows10x64.spec --additional-hooks-dir=.
2) run & compile innosetup_Windows10x64.iss
#### OSX running an intel chip:
1) change paths in pyinstaller-OSX.spec to where your python site-packages are installed
2) python -m PyInstaller --windowed --additional-hooks-dir=. pyinstaller-OSX.spec
3) run & build packages_OSX_x86_64.pkgproj
#### OSX running an M1 chip:
1) change paths in pyinstaller-OSX.spec to where your python site-packages are installed
2) python -m PyInstaller --windowed --additional-hooks-dir=. pyinstaller-OSX.spec
3) run & build packages_OSX_arm64.pkgproj

### Needed applications
- python 3.9
- pyinstaller 4.5.1 - For Windows
- Inno Setup Compiler - For Windows
- packages - For OSX

### Needed Packages (there may be others)
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
- pip install pytz
- pip install lxml
- pip install xmlschema
- pip install scikit-learn==1.0.1

### Additional Steps
- python -m spacy download fr_core_news_sm
- python -m spacy download en_core_web_sm
