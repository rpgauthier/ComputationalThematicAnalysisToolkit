# HOOK FILE FOR SPACY
from PyInstaller.utils.hooks import collect_all

# ----------------------------- SPACY -----------------------------
print('=================== SPACY =====================')
data = collect_all('spacy')

datas = data[0]
binaries = data[1]
hiddenimports = data[2]

# ----------------------------- THINC -----------------------------
data = collect_all('thinc')

datas += data[0]
binaries += data[1]
hiddenimports += data[2]

# ----------------------------- CYMEM -----------------------------
data = collect_all('cymem')

datas += data[0]
binaries += data[1]
hiddenimports += data[2]

print(data[2])

# ----------------------------- PRESHED -----------------------------
data = collect_all('preshed')

datas += data[0]
binaries += data[1]
hiddenimports += data[2]

# ----------------------------- BLIS -----------------------------

data = collect_all('blis')

datas += data[0]
binaries += data[1]
hiddenimports += data[2]

# ----------------------------- OTHER ----------------------------

hiddenimports += ['srsly.msgpack.util']


from PyInstaller.utils.hooks import collect_data_files
datas += collect_data_files("en_core_web_sm")
datas += collect_data_files("en_core_web_trf")
datas += collect_data_files("fr_core_news_sm")

# This hook file is a bit of a hack - really, all of the libraries should be in seperate hook files. (Eg hook-blis.py with the blis part of the hook)
# But it looks we need to process everything when we import spacy, else we do not even hit import cymem.

print('=================== SPACY DONE =====================')