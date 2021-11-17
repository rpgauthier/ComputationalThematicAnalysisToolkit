import xmlschema
import xml.etree.ElementTree as ET
import platform
import uuid
from datetime import datetime
from zipfile import ZipFile
from os.path import basename

import Common.Constants as Constants
import Common.Objects.Datasets as Datasets
import Common.Objects.Samples as Samples
import Common.Objects.Codes as Codes

def QDAProjectExporter(name, datasets, samples, codes, file_name, archive_name):
    project_element = ET.Element('Project')
    #setup root elements
    project_element.set('xmlns', "urn:QDA-XML:project:1.0")
    project_element.set('xmlns:xsd', "urn:QDA-XML:project:1.0")
    project_element.set('xmlns:xsi', "http://www.w3.org/2001/XMLSchema-instance")
    project_element.set('xsi:schemaLocation', "urn:QDA-XML:project:1.0 http://schema.qdasoftware.org/versions/Project/v1.0/Project.xsd")
    #onfigure project variables
    project_element.set('name', name)
    project_element.set('origin', 'ComputationalThematicAnalysisToolkit')

    codebook_element = ET.SubElement(project_element, 'CodeBook')
    codes_element = ET.SubElement(codebook_element, 'Codes')
    def CodeToCodeElement(parent_element, code):
        new_code_element = ET.SubElement(parent_element, 'Code')
        new_code_element.set('guid', code.key)
        new_code_element.set('name', code.name)
        new_code_element.set('isCodable', 'true')
        new_code_element.set('color', '#%02x%02x%02x' % code.colour_rgb)
        desc = ET.SubElement(new_code_element, 'Description')
        if isinstance(code.notes, bytes):
            desc.text = code.notes_string
        else:
            desc.text = code.notes
        for subcode_key in code.subcodes:
            CodeToCodeElement(new_code_element, code.subcodes[subcode_key])

    for code_key in codes:
        if codes[code_key].parent == None:
            CodeToCodeElement(codes_element, codes[code_key])
    
    if len(codes_element.findall('Code')) == 0:
        project_element.remove(codebook_element)

    cases_element = ET.SubElement(project_element, 'Cases')
    sources_element = ET.SubElement(project_element, 'Sources')

    added_documents = []

    def DocumentToSourceElement(dataset, document):
        new_source_element = ET.SubElement(sources_element, 'TextSource')
        new_source_element.set('guid', document.key)
        new_source_element.set('name', document.doc_id)
        added_fields = {}
        cur_pos = 0
        field_str = ""
        for field in dataset.label_fields.values():
            if field.key not in added_fields:
                if field.fieldtype == 'UTC-timestamp':
                    field_str = field_str + datetime.utcfromtimestamp(dataset.data[document.doc_id][field.name]).strftime(Constants.DATETIME_FORMAT)
                    field_str = field_str + '\n------------\n'
                else:
                    field_str = field_str + str(dataset.data[document.doc_id][field.name])
                    field_str = field_str + '\n------------\n'
                added_fields[field.key] = cur_pos
                cur_pos = len(field_str)
        for field in dataset.computational_fields.values():
            if field.key not in added_fields:
                if field.fieldtype == 'UTC-timestamp':
                    field_str = datetime.utcfromtimestamp(dataset.data[document.doc_id][field.name]).strftime(Constants.DATETIME_FORMAT)
                    field_str = field_str + '\n------------\n'
                else:
                    field_str = str(dataset.data[document.doc_id][field.name])
                    field_str = field_str + '\n------------\n'
                added_fields[field.key] = cur_pos
                cur_pos = len(field_str)
        new_plaintextcontent_element = ET.SubElement(new_source_element, 'PlainTextContent')
        new_plaintextcontent_element.text = field_str
        for code in document.GetCodeConnections(codes):
            if (dataset.key, document.key) in code.doc_positions:
                for position in code.doc_positions[(dataset.key, document.key)]:
                    new_selection_element = ET.SubElement(new_source_element, 'PlainTextSelection')
                    new_selection_element.set('guid', str(uuid.uuid4()))
                    new_selection_element.set('startPosition', str(position[1] + added_fields[position[0]]))
                    new_selection_element.set('endPosition', str(position[2] + added_fields[position[0]]))
                    new_coding_element = ET.SubElement(new_selection_element, 'Coding')
                    new_coding_element.set('guid', str(uuid.uuid4()))
                    new_code_ref = ET.SubElement(new_coding_element, 'CodeRef')
                    new_code_ref.set('targetGUID', code.key)
        for code in document.GetCodeConnections(codes):
            new_coding_element = ET.SubElement(new_source_element, 'Coding')
            new_coding_element.set('guid', str(uuid.uuid4()))
            new_code_ref = ET.SubElement(new_coding_element, 'CodeRef')
            new_code_ref.set('targetGUID', code.key)
        added_documents.append(document.key)

    for dataset in datasets.values():
        new_case = ET.SubElement(cases_element, 'Case')
        new_case.set('guid', dataset.key)
        new_case.set('name', dataset.name)
        for document_key in dataset.selected_documents:
            document = dataset.documents[document_key]
            if document.key not in added_documents:
                DocumentToSourceElement(dataset, document)
            new_source_ref = ET.SubElement(new_case, 'SourceRef')
            new_source_ref.set('targetGUID', document.key)
    
    for sample in samples.values():
        new_case = ET.SubElement(cases_element, 'Case')
        new_case.set('guid', sample.key)
        new_case.set('name', sample.name)
        dataset = datasets[sample.dataset_key]
        for document_key in sample.selected_documents:
            document = dataset.documents[document_key]
            if document.key not in added_documents:
                DocumentToSourceElement(dataset, document)
            new_source_ref = ET.SubElement(new_case, 'SourceRef')
            new_source_ref.set('targetGUID', document.key)

    if len(sources_element.findall('TextSource')) == 0:
        project_element.remove(sources_element)

    if len(cases_element.findall('Case')) == 0:
        project_element.remove(cases_element)

    tree = ET.ElementTree(project_element)

    tree.write(file_name)
    #TODO figure out why function is failing with no exception on OSX after pyinstaller
    if platform.system() == 'Windows':
        codebook_schema = xmlschema.XMLSchema('./External/REFI-QDA/Project-mrt2019.xsd')
        codebook_schema.validate(file_name)
    
    with ZipFile(archive_name, 'w') as zipObj:
        zipObj.write(file_name, basename(file_name))


#TODO NOT IMPLIMENTED
def QDAProjectImporter(pathname):
    datasets = {}
    samples = {}
    codes = {}
    
    #bring in generic objects and return to allow application to work with user to upgrade existing project?

    return datasets, samples, codes
def QDACodeExporter(codes, file_name):
    codebook_element = ET.Element('CodeBook')
    codebook_element.set('origin', 'ComputationalThematicAnalysisToolkit')
    codebook_element.set('xmlns', "urn:QDA-XML:codebook:1.0")
    codebook_element.set('xmlns:xsd', "urn:QDA-XML:codebook:1.0")
    codebook_element.set('xmlns:xsi', "http://www.w3.org/2001/XMLSchema-instance")
    codebook_element.set('xsi:schemaLocation', "urn:QDA-XML:codebook:1.0 http://schema.qdasoftware.org/versions/Codebook/v1.0/Codebook.xsd")
    codes_element = ET.SubElement(codebook_element, 'Codes')

    def CodeToCodeElement(parent_element, code):
        new_code_element = ET.SubElement(parent_element, 'Code')
        new_code_element.set('guid', code.key)
        new_code_element.set('name', code.name)
        new_code_element.set('isCodable', 'true')
        new_code_element.set('color', '#%02x%02x%02x' % code.colour_rgb)
        desc = ET.SubElement(new_code_element, 'Description')
        if isinstance(code.notes, bytes):
            desc.text = code.notes_string
        else:
            desc.text = code.notes
        for subcode_key in code.subcodes:
            CodeToCodeElement(new_code_element, code.subcodes[subcode_key])

    for code_key in codes:
        if codes[code_key].parent == None:
            CodeToCodeElement(codes_element, codes[code_key])

    tree = ET.ElementTree(codebook_element)

    tree.write(file_name)
    #TODO figure out why function is failing with no exception on OSX after pyinstaller
    if platform.system() == 'Windows':
        codebook_schema = xmlschema.XMLSchema('./External/REFI-QDA/Codebook-mrt2019.xsd')
        codebook_schema.validate(file_name)

def QDACodeImporter(file_name):
    codes = {}
    #TODO figure out why function is failing with no exception on OSX after pyinstaller
    if platform.system() == 'Windows':
        codebook_schema = xmlschema.XMLSchema('./External/REFI-QDA/Codebook-mrt2019.xsd')
        codebook_schema.validate(file_name)

    tree = ET.parse(file_name)
    codebook_element = tree.getroot()

    def CodeElementToCode(code_element):
        code = Codes.Code(code_element.attrib['name'], code_element.attrib['guid'])
        color_hex = code_element.attrib['color'].lstrip('#')
        code.colour_rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
        notes = ""
        for child in list(code_element):
            if child.tag == '{urn:QDA-XML:codebook:1.0}Description':
                if child.text != None:
                    notes = notes + child.text
            if child.tag == '{urn:QDA-XML:codebook:1.0}Code':
                subcode = CodeElementToCode(child)
                subcode.parent = code
                code.subcodes[subcode.key] = subcode
        code.notes = notes
        code.notes_string = notes
        return code

    for child in list(codebook_element):
        if child.tag == '{urn:QDA-XML:codebook:1.0}Codes':
            codes_element = child
            for code_element in list(codes_element):
                code = CodeElementToCode(code_element)
                codes[code.key] = code
    return codes