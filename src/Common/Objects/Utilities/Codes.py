import wx

from Common.GUIText import Coding as GUIText

def CodeKeyUniqueCheck(new_code_key, existing_codes):
    if new_code_key in existing_codes:
        return False
    else:
        for existing_code_key in existing_codes:
            if not CodeKeyUniqueCheck(new_code_key, existing_codes[existing_code_key].subcodes):
                return False
        return True
