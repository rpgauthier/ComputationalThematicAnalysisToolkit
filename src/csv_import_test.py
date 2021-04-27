import csv

path = "C:/Users/Robert Gauthier/Documents/School/PHD_Studies/Autobiographical Design/Toolkit/Data/COVID/"
filename = "Covid_Good_Confidence_Results_v2.csv" 

raw_dataset = []

with open(path+filename, mode='r', encoding='utf-8') as infile:
    reader = csv.reader(infile)
    header_row = next(reader)
    for row in reader:
        data_row = {header_row[i]: row[i] for i in range(len(header_row))}
        raw_dataset.append(data_row)

comment_data = {}
for comment in raw_dataset:
    key = ("CSV", "comment", comment['Comment ID'])
    comment_data[key] = comment
    comment_data[key]["data_source"] = "CSV"
    comment_data[key]["data_type"] = "comment"

print(list(comment_data.keys())[0])
print(comment_data[list(comment_data.keys())[0]])