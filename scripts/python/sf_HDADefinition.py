import hou
import xml.etree.ElementTree as ET
import gzip
import sys
import io


def getinfo(node):
  
    hda_def = node.type().definition()
    sec = hda_def.sections()
    print('************Section *******************')
    for key in sec.keys():
        print(key)
    '''
        Contents.gz
        CreateScript
        DialogScript
        ExtraFileOptions
        Help
        InternalFileOptions
        Tools.shelf
        TypePropertiesOptions
    '''
    # DialogScript
    print("\n************************Contents.gz***************")
    # file_obj = io.BytesIO(sec["Contents.gz"].binaryContents())
    # gzip_file = gzip.GzipFile(fileobj=file_obj, mode="r")
    # print(gzip_file.read())

    # DialogScript
    print("\n************************Tools.shelf***************")
    dialog_content = sec['DialogScript'].contents()
    dialog_content.replace("name    valar_mask_clamp","name    sss")
    print(dialog_content)

    hda_def.addSection('DialogScript',dialog_content)
    # Tools.shelf
    print("\n************************Tools.shelf***************")
    tool_content = sec['Tools.shelf'].contents()
    print(tool_content)

    # TypePropertiesOptions info
    print("\n************TypePropertiesOptions******************")
    print(sec['TypePropertiesOptions'].contents())

    # file_obj = io.BytesIO(sec["INDEX__SECTION"].binaryContents())
    # gzip_file = gzip.GzipFile(fileobj=file_obj, mode="r")
    # print(gzip_file.read())
