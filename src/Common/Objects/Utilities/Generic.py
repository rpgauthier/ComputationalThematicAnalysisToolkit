import xmlschema
import lxml.etree as ET
import platform
import uuid
from datetime import datetime
from zipfile import ZipFile, ZipInfo
from os.path import basename

import wx

from Common.GUIText import Main as GUIText
import Common.Constants as Constants
import Common.Objects.Datasets as Datasets
import Common.Objects.Samples as Samples
import Common.Objects.Codes as Codes

def QDAProjectExporter(name, datasets, samples, codes, themes, file_name, archive_name):
    #setup root element
    project_element = ET.Element('Project',
                                 nsmap={'xsd':"http://www.w3.org/2001/XMLSchema",
                                        'xsi': "http://www.w3.org/2001/XMLSchema-instance",
                                        None: "urn:QDA-XML:project:1.0"
                                        })
    #configure project variables
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

    cases_element = ET.SubElement(project_element, 'Cases')
    sources_element = ET.SubElement(project_element, 'Sources')

    included_documents = {}

    def DocumentToSourceElement(dataset, document):
        new_source_element = ET.SubElement(sources_element, 'TextSource')
        new_source_element.set('guid', document.key)
        new_source_element.set('name', str(document.doc_id))
        added_fields = {}
        cur_pos = 0
        text_str = ""
        for field in dataset.label_fields.values():
            text_str = text_str+'------'+str(field.name)+'------\n'
            if field.key not in added_fields:
                if field.fieldtype == 'UTC-timestamp':
                    text_str = text_str + datetime.utcfromtimestamp(dataset.data[document.doc_id][field.name]).strftime(Constants.DATETIME_FORMAT)
                    text_str = text_str + '\n------------\n'
                else:
                    text_str = text_str + str(dataset.data[document.doc_id][field.name])
                    text_str = text_str + '\n------------\n'
                added_fields[field.key] = cur_pos
                cur_pos = len(text_str)
        for field in dataset.computational_fields.values():
            if field.key not in added_fields:
                text_str = text_str+'------'+str(field.name)+'------\n'
                if field.fieldtype == 'UTC-timestamp':
                    text_str = text_str + datetime.utcfromtimestamp(dataset.data[document.doc_id][field.name]).strftime(Constants.DATETIME_FORMAT)
                    text_str = text_str + '\n------------\n'
                else:
                    text_str = text_str + str(dataset.data[document.doc_id][field.name])
                    text_str = text_str + '\n------------\n'
                added_fields[field.key] = cur_pos
                cur_pos = len(text_str)
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
            else:
                new_selection_element = ET.SubElement(new_source_element, 'PlainTextSelection')
                new_selection_element.set('guid', str(uuid.uuid4()))
                new_selection_element.set('startPosition', str(0))
                new_selection_element.set('endPosition', str(len(text_str)))
                new_coding_element = ET.SubElement(new_selection_element, 'Coding')
                new_coding_element.set('guid', str(uuid.uuid4()))
                new_code_ref = ET.SubElement(new_coding_element, 'CodeRef')
                new_code_ref.set('targetGUID', code.key)
        new_source_element.set('plainTextPath', "internal://"+str(document.key)+".txt")
        included_documents[document.key] = text_str

    for dataset in datasets.values():
        new_case = ET.SubElement(cases_element, 'Case')
        new_case.set('guid', dataset.key)
        new_case.set('name', dataset.name)
        for document_key in dataset.selected_documents:
            document = dataset.documents[document_key]
            if document.key not in included_documents:
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
            if document.key not in included_documents:
                DocumentToSourceElement(dataset, document)
            new_source_ref = ET.SubElement(new_case, 'SourceRef')
            new_source_ref.set('targetGUID', document.key)

    if len(sources_element.findall('TextSource')) == 0:
        project_element.remove(sources_element)

    if len(cases_element.findall('Case')) == 0:
        project_element.remove(cases_element)
    
    if len(codes_element.findall('Code')) == 0:
        project_element.remove(codebook_element)

    sets_element = ET.SubElement(project_element, 'Sets')
    def ThemeToSetElement(theme, parent_labels):
        new_set_element = ET.SubElement(sets_element, 'Set')
        new_set_element.set('guid', theme.key)
        new_set_element.set('name', parent_labels+theme.name)
        desc = ET.SubElement(new_set_element, 'Description')
        if isinstance(theme.notes, bytes):
            desc.text = theme.notes_string
        else:
            desc.text = theme.notes
        for subtheme_key in theme.subthemes:
            ThemeToSetElement(theme.subthemes[subtheme_key], parent_labels+theme.name+"_")
        for code_key in theme.code_keys:
            new_member_code = desc = ET.SubElement(new_set_element, 'MemberCode')
            new_member_code.set('targetGUID', code_key)

    for theme_key in themes:
        if themes[theme_key].parent == None:
            ThemeToSetElement(themes[theme_key], "")
    
    if len(sets_element.findall('Set')) == 0:
        project_element.remove(sets_element)

    tree = ET.ElementTree(project_element)

    tree.write(file_name, encoding='utf-8', xml_declaration=True, pretty_print=True)
    codebook_schema = xmlschema.XMLSchema('./External/REFI-QDA/Project-mrt2019.xsd')
    codebook_schema.validate(file_name)
    
    with ZipFile(archive_name, 'w') as zipObj:
        zipObj.write(file_name, basename(file_name))
        zipObj.writestr(ZipInfo("Sources/"), '')
        for document_key in included_documents:
            zipObj.writestr(ZipInfo("Sources/"+str(document_key)+".txt"), included_documents[document_key])

#TODO NOT YET IMPLIMENTED
def QDAProjectImporter(pathname):
    datasets = {}
    samples = {}
    codes = {}
    themes = {}
    
    #bring in generic objects and return to allow application to work with user to upgrade existing project?

    return datasets, samples, codes

def QDACodeExporter(codes, themes, file_name):
    attr_qname = ET.QName("http://www.w3.org/2001/XMLSchema-instance", "schemaLocation")
    codebook_element = ET.Element('CodeBook',
                                  {attr_qname: 'urn:QDA-XML:codebook:1.0 Codebook.xsd'},
                                  nsmap={None: 'urn:QDA-XML:codebook:1.0',
                                         'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                                         })
    codebook_element.set('origin', 'ComputationalThematicAnalysisToolkit')
    
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

    sets_element = ET.SubElement(codebook_element, 'Sets')
    def ThemeToSetElement(theme, parent_label):
        new_set_element = ET.SubElement(sets_element, 'Set')
        new_set_element.set('guid', theme.key)
        new_set_element.set('name', theme.name)
        desc = ET.SubElement(new_set_element, 'Description')
        if parent_label != "":
            parent_text = "sub-theme of " + parent_label + "\n"
        else:
            parent_text = ""
        if isinstance(theme.notes, bytes):
            desc.text = parent_text + theme.notes_string
        else:
            desc.text = parent_text + theme.notes
        for subtheme_key in theme.subthemes:
            ThemeToSetElement(theme.subthemes[subtheme_key], theme.name)
        for code_key in theme.code_keys:
            new_member_code = desc = ET.SubElement(new_set_element, 'MemberCode')
            new_member_code.set('guid', code_key)

    for theme_key in themes:
        if themes[theme_key].parent == None:
            ThemeToSetElement(themes[theme_key], "")
    
    if len(sets_element.findall('Set')) == 0:
        codebook_element.remove(sets_element)

    tree = ET.ElementTree(codebook_element)

    tree.write(file_name, encoding='utf-8', xml_declaration=True, pretty_print=True)
    codebook_schema = xmlschema.XMLSchema('./External/REFI-QDA/Codebook-mrt2019.xsd')
    codebook_schema.validate(file_name)

def QDACodeImporter(file_name):
    codes = {}
    themes = {}
    
    #TODO validation issues with the files generated by both MaxQDA and NVIVO
    #appears to be due to different version number in xml namespaces (0:4 and 1:0 instead of expected 1.0)
    #if platform.system() == 'Windows':
    #    codebook_schema = xmlschema.XMLSchema('./External/REFI-QDA/Codebook-mrt2019.xsd')
    #    codebook_schema.validate(file_name)

    tree = ET.parse(file_name)
    codebook_element = tree.getroot()

    def CodeElementToCode(code_element):
        code = Codes.Code(code_element.attrib['name'], key=code_element.attrib['guid'])
        if 'color' in code_element.attrib:
            color_hex = code_element.attrib['color'].lstrip('#')
            code.colour_rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
        notes = ""
        for child in list(code_element):
            if 'Description' in child.tag:
                if child.text != None:
                    notes = notes + child.text
            if 'Code' in child.tag:
                subcode = CodeElementToCode(child)
                subcode.parent = code
                code.subcodes[subcode.key] = subcode
        code.notes = notes
        code.notes_string = notes
        return code
    
    def SetElementToTheme(set_element):
        theme = Codes.Theme(set_element.attrib['name'], key=set_element.attrib['guid'])
        notes = ""
        for child in list(set_element):
            if 'Description' in child.tag:
                if child.text != None:
                    notes = notes + child.text
            if 'MemberCode' in child.tag:
                theme.code_keys.append(child.attrib['guid'])
        theme.notes = notes
        theme.notes_string = notes
        return theme

    for child in list(codebook_element):
        if 'Codes' in child.tag:
            codes_element = child
            for code_element in list(codes_element):
                code = CodeElementToCode(code_element)
                codes[code.key] = code
        if 'Sets' in child.tag:
            sets_element = child
            for set_element in list(sets_element):
                theme = SetElementToTheme(set_element)
                themes[theme.key] = theme
        
    return codes, themes

def IntegrateImportedCodes(main_frame, imported_codes):
    def MergeCodes(new_codes):
        for new_key in list(new_codes.keys()):
            new_code = new_codes[new_key]
            MergeCodes(new_code.subcodes)
            #Recurively find existing code if it exists
            def FindCode(sought_code, codes):
                if sought_code.key in codes:
                    return codes[sought_code.key]
                else:
                    for key in codes:
                        found_code = FindCode(sought_code, codes[key].subcodes)
                        if found_code != None:
                            return found_code
                return None
            found_code = FindCode(new_code, main_frame.codes)
            if found_code != None:
                #if it does exist ask user if they want to keep both, merge import into imported, merge existing into existing
                action_dialog = wx.MessageDialog(main_frame, "Imported Code ["+new_code.name+"] already exists as Code ["+found_code.name+"]."\
                                                        "\nWhat action would you like to take?",
                                                    GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.YES_NO | wx.CANCEL)
                action_dialog.SetYesNoCancelLabels("Import as new Code", "Update Existing Code", "Skip")
                action = action_dialog.ShowModal()

                if action == wx.ID_YES:
                    old_key = new_code.key
                    new_code.key = str(uuid.uuid4())
                    new_codes[new_code.key] = new_code
                    del new_codes[old_key]
                elif action == wx.ID_NO:
                    for existing_subcode_key in list(found_code.subcodes.keys()):
                        existing_subcode = found_code.subcodes[existing_subcode_key]
                        if FindCode(existing_subcode, imported_codes) == None:
                            existing_subcode.parent = new_code
                            new_code.subcodes[existing_subcode.key] = existing_subcode
                            del found_code.subcodes[existing_subcode_key]
                    new_code.connections = found_code.connections
                    found_code.connections = []
                    new_code.doc_positions = found_code.doc_positions
                    found_code.doc_positions = {}
                    new_code.quotations = found_code.quotations
                    for quotation in new_code.quotations:
                        quotation.parent = new_code
                    found_code.quotations = []
                    found_code.DestroyObject()
                elif action == wx.CANCEL:
                    new_code.DestroyObject()
    MergeCodes(imported_codes)
    for code_key in imported_codes:
        main_frame.codes[code_key] = imported_codes[code_key]

def IntegrateImportedThemes(main_frame, new_themes):
    #handle merges for any subthemes that already exist
    def SubThemeMerger(subthemes):
        for subtheme_key in subthemes:
            existing_subtheme = main_frame.themes[subtheme_key]
            new_theme = new_themes[subtheme_key]
            action_dialog = wx.MessageDialog(main_frame,
                                                "Imported Theme ["+new_theme.name+"] existed as a SubTheme ["+existing_subtheme.name+"] of ["+existing_subtheme.parent.name+"]."\
                                                "\nWhat action would you like to take?",
                                                GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.YES_NO | wx.CANCEL)
            action_dialog.SetYesNoCancelLabels("Import as new Theme", "Update Existing SubTheme", "Skip")
            action = action_dialog.ShowModal()
            if action == wx.ID_YES:
                new_theme.key = str(uuid.uuid4())
                subthemes[new_theme.key] = new_theme
                del new_theme[subtheme_key]
            elif action == wx.ID_NO:
                existing_subtheme.name = new_theme.name
                existing_subtheme.notes = new_theme.notes
                existing_subtheme.notes_string = new_theme.notes_string
                existing_subtheme.code_keys = new_theme.code_keys
                del new_theme[subtheme_key]
            else:
                del new_theme[subtheme_key]
            SubThemeMerger(existing_subtheme.subthemes)
    #handle merges for any themes that already exist
    for theme_key in main_frame.themes:
        if theme_key in new_themes:
            existing_theme = main_frame.themes[theme_key]
            new_theme = new_themes[theme_key]
            action_dialog = wx.MessageDialog(main_frame,
                                             "Imported Theme ["+new_theme.name+"] existed as Theme ["+existing_theme.name+"]."\
                                             "\nWhat action would you like to take?",
                                             GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.YES_NO | wx.CANCEL)
            action_dialog.SetYesNoCancelLabels("Import as new Theme", "Update Existing Theme", "Skip")
            action = action_dialog.ShowModal()
            if action == wx.ID_YES:
                new_theme.key = str(uuid.uuid4())
                main_frame.themes[new_theme.key] = new_theme
                del new_theme[theme_key]
            elif action == wx.ID_NO:
                existing_theme.name = new_theme.name
                existing_theme.notes = new_theme.notes
                existing_theme.notes_string = new_theme.notes_string
                existing_theme.code_keys = new_theme.code_keys
                del new_theme[theme_key]
            else:
                del new_theme[theme_key]
            SubThemeMerger(existing_theme.subthemes)

    #import any themes that did not already exist
    for new_theme_key in new_themes:
        main_frame.themes[new_theme_key] = new_themes[new_theme_key]

def BackgroundAndForegroundColour(colour_rgb):
    bg_colour = wx.Colour(colour_rgb[0], colour_rgb[1], colour_rgb[2])
    colours = []
    for c in colour_rgb:
        c = c / 255.0
        if c <= 0.03928:
            c = c/12.92
        else:
            c = ((c+0.055)/1.055) ** 2.4
        colours.append(c)
    L = 0.2126 * colours[0] + 0.7152 * colours[1] + 0.0722 * colours[2]
    if L > 0.179:
        fg_colour = wx.Colour(0, 0, 0)
    else:
       fg_colour = wx.Colour(255, 255, 255)
    return bg_colour, fg_colour