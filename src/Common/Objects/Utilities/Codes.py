import xmlschema
import xml.etree.ElementTree as ET
import Common.Objects.Codes as Codes

def QDACodeExporter(codes, pathname):
    codebook_element = ET.Element('CodeBook')
    codebook_element.set('origin', 'ComputationalThematicAnalysisToolkit')
    codebook_element.set('xmlns', "urn:QDA-XML:codebook:1.0")
    codebook_element.set('xmlns:xsd', "urn:QDA-XML:codebook:1.0")
    codebook_element.set('xmlns:xsi', "http://www.w3.org/2001/XMLSchema-instance")
    codebook_element.set('xsi:schemaLocation', "urn:QDA-XML:codebook:1.0 http://schema.qdasoftware.org/versions/Codebook/v1.0/Codebook.xsd")
    codes_element = ET.SubElement(codebook_element, 'Codes')

    def CodeToCodeElement(parent_element, code):
        new_code_element = ET.SubElement(parent_element, 'Code')
        new_code_element.set('guid', code.uuid)
        new_code_element.set('name', code.name)
        new_code_element.set('isCodable', 'true')
        new_code_element.set('color', '#%02x%02x%02x' % code.colour_rgb)
        desc = ET.SubElement(new_code_element, 'Description')
        if isinstance(code.notes, bytes):
            #TODO need to figure out how to convert from richtext buffer back to string
            desc.text = ""
        else:
            desc.text = code.notes
        for subcode_key in code.subcodes:
            CodeToCodeElement(new_code_element, codes[subcode_key])

    for code_key in codes:
        if codes[code_key].parent == None:
            CodeToCodeElement(codes_element, codes[code_key])

    tree = ET.ElementTree(codebook_element)

    tree.write(pathname)
    codebook_schema = xmlschema.XMLSchema('./External/REFI-QDA/Codebook-mrt2019.xsd')
    codebook_schema.validate(pathname)

def QDACodeImporter(pathname):
    codes = {}
    codebook_schema = xmlschema.XMLSchema('./External/REFI-QDA/Codebook-mrt2019.xsd')
    codebook_schema.validate(pathname)

    tree = ET.parse(pathname)
    codebook_element = tree.getroot()
    print(ET.tostring(codebook_element, encoding='utf8').decode('utf8'))

    def CodeElementToCode(code_element):
        code = Codes.Code(code_element.attrib['name'])
        code.key = code_element.attrib['guid']
        code.uuid = code_element.attrib['guid']
        color_hex = code_element.attrib['color'].lstrip('#')
        code.colour_rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
        notes = ""
        for child in list(code_element):
            if child.tag == '{urn:QDA-XML:codebook:1.0}Description':
                if child.text != None:
                    notes = notes + child.text
            if child.tag == '{urn:QDA-XML:codebook:1.0}Code':
                subcode = CodeElementToCode(child)
                code.subcodes[subcode.key] = subcode
        code.notes = notes
        return code

    for child in list(codebook_element):
        if child.tag == '{urn:QDA-XML:codebook:1.0}Codes':
            codes_element = child
            for code_element in list(codes_element):
                code = CodeElementToCode(code_element)
                codes[code.key] = code
    return codes