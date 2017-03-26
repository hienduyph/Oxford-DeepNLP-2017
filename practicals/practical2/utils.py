import os
import urllib.request as request
import zipfile
import lxml.etree as ET
import re

FILENAME = "ted_en-20160408.zip"
XMLNAME = "ted_en-20160408.xml"


def load_dataset():
    maybe_download_file()
    with zipfile.ZipFile(FILENAME, "R") as z:
        data = ET.parse(z.open(XMLNAME, "r"))
    texts = "\n".join(data.xpath("//content/text()"))
    labels = "\n".join(data.xpath("//keywords/text()"))
    texts = _preprocessing_text(texts)
    labels = _preprocessing_label(labels)
    return (texts, labels)


def maybe_download_file():
    URL = "https://wit3.fbk.eu/get.php?path=XML_releases/xml/{}&filename={}"\
        .format(FILENAME, FILENAME)
    if not os.path.isfile(FILENAME):
        request.urlretrieve(URL, filename=FILENAME)


def _preprocessing_text(text):
    """This preprocessing function based on the first practical"""
    # Remove all parenthesized strings
    text = re.sub(r"\([^)]*\)", "", text)
    # Remove the speakers' names that occur at the beginning of a line
    # by deleting pieces of the form "<20 characters>:"
    sentences = []
    for line in text.split("\n"):
        m = re.match(r"^(?:(?P<precolon>[^:]{,20}):)?(?P<postcolon>.*)$", line)
        sentences.extend(
            sent for sent in m.groupdict()['postcolon'].split(".") if sent)

    # Start to tokenize the string
    sentences_tokenized = []
    for sent in sentences:
        tokens = re.sub(r"[^a-z0-9]", " ", sent.lower().split())
        sentences_tokenized.append(tokens)
    return sentences_tokenized


def _preprocessing_label(labels):
    """
    Rule for labeling
    - None of the keywords → ooo
    - “Technology” → Too
    - “Entertainment” → oEo
    - “Design” → ooD
    - “Technology” and “Entertainment” → TEo
    - “Technology” and “Design” → ToD
    - “Entertainment” and “Design” → oED
    - “Technology” and “Entertainment” and “Design” → TED
    """
    labels = labels.split("\n")
    map(_keywords_numeric, labels)
    map(_encode_label, labels)
    return labels


def _encode_label(label):
    """
    For convenient:
        Technology = 1
        Entertainment = 2
        Design = 3
        Other = 4

    Label is a set of numeric keyword
    - None of the keywords: empty set → ooo
    - “Technology”: set(1) → Too
    - “Entertainment”: set(2) → oEo
    - “Design”: set(3) → ooD
    - “Technology” and “Entertainment”: set(1, 2) → TEo
    - “Technology” and “Design”: set(1, 3) → ToD
    - “Entertainment” and “Design”: set(2, 3) → oED
    - “Technology” and “Entertainment” and “Design”: set(1, 2, 3) → TED
    """
    # Becareful that the conditions is checked in order
    if set(1, 2, 3).issubset(label):
        return "TED"
    if set(1, 2).issubset(label):
        return "TEo"
    if set(1, 3).issubset(label):
        return "ToD"
    if set(2, 3).issubset(label):
        return "oED"
    if set(1).issubset(label):
        return "Too"
    if set(2).issubset(label):
        return "oEo"
    if set(3).issubset(label):
        return "ooD"
    return "ooo"


def _keywords_numeric(keywords):
    """
    For convenient:
        Technology = 1
        Entertainment = 2
        Design = 3
        Other = 4
    """
    keywords = [keyword.strip().lower() for keyword in keywords.split(",")]

    def _numeric(keyword):
        if keyword == "technology":
            return 1
        if keyword == "entertainment":
            return 2
        if keyword == "deisgn":
            return 3
        return 4

    map(_numeric, keywords)
    return set(keywords)
