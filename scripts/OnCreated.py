import hou


def wranglePresets(kwargs):
    node = kwargs["node"]
    if (node.type().name() == "attribwrangle"):
        node.setColor(hou.Color(1, 0, 0))
        # node.setUserData("nodeshape", "gurgle")


def nullPresets(kwargs):
    node = kwargs["node"]
    if (node.type().name() == "null"):
        node.setColor(hou.Color(0, 0.7, 0))


def dopPresets(kwargs):
    node = kwargs["node"]
    if (node.type().name() == "dopnet"):
        node.setColor(hou.Color(0.8, 0.016, 0.016))


def objmergePresets(kwargs):
    node = kwargs["node"]
    if (node.type().name() == "object_merge"):
        node.setColor(hou.Color(0.5, 0, 1))


def filePresets(kwargs):
    node = kwargs["node"]
    if (node.type().name() == "file"):
        node.parm("missingframe").set("empty")


wranglePresets(kwargs)
nullPresets(kwargs)
dopPresets(kwargs)
objmergePresets(kwargs)
filePresets(kwargs)
