
"""This is a work in progress and should not be used.
It is pre-deprecated (preprecated?).
"""

import config

import runner

defaultAttributes = {}

def registerDataset(ds, attributes=None):

    if attributes is None: attributes = defaultAttributes
    attrs = ' '.join(["--define %s=%s" % pair for pair in attributes.items()])

    dcClient = config.dcClient

    group = ds.dcGroup
    format = ds.fileFormat
    site = ds.site
    version = ds.version
    name = ds.dsName
    dataType = ds.dcType
    folder = ds.dataCatDir
    fileName = ds.fileName

    cmd = "%(dcClient)s registerDataset --group %(group)s --format %(format)s --site %(site)s --version %(version)s %(attrs)s --name %(name)s %(dataType)s %(folder)s %(fileName)s" % locals()
    
    return


class NewDataset(object):

    def __init__(self,
                 dsName,
                 fileFormat,
                 dcType,
                 dataCatDir,
                 dcGroup,
                 site,
                 fileName):
        self.dsName = dsName
        self.fileFormat = fileFormat
        self.dcType = dcType
        self.dataCatDir = dataCatDir
        self.dcGroup = dcGroup
        self.site = site
        self.fileName = fileName
        return

    def setVersionID(self, version):
        self.version = version
        return

    pass
