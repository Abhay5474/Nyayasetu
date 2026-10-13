from app.processing.chunking import chunk_text
from app.processing.cleaning import clean_pages, detect_language


def test_clean_joins_wrapped_lines_and_removes_page_numbers():
    pages = ["The Public Information Officer shall\nprovide the information within\n30 days.\n\n- 1 -", "Page 2 of 2\nSecond page text here."]
    out = clean_pages(pages)
    assert "shall provide the information within 30 days." in out
    assert "Page 2 of 2" not in out and "- 1 -" not in out


def test_clean_removes_repeated_headers():
    topics = ["fees", "appeal", "penalty", "transfer", "inspection"]
    pages = [f"GOVERNMENT OF MAHARASHTRA\nThe {t} rules are explained here with real content that matters.\nPage {i}" for i, t in enumerate(topics, 1)]
    out = clean_pages(pages)
    assert "GOVERNMENT OF MAHARASHTRA" not in out
    assert out.count("real content") == 5


def test_clean_dehyphenates_and_normalises_marathi():
    out = clean_pages(["माहितीचा अधिकार​ अधिनियम\nअंतर्गत अर्ज केला आहे.", "inform-\nation request."])
    assert "​" not in out
    assert "अधिनियम अंतर्गत अर्ज केला आहे." in out
    assert "information request." in out


def test_detect_language():
    assert detect_language("The applicant has filed a first appeal under Section 19 of the Act.") == "en"
    assert detect_language("अर्जदाराने माहितीचा अधिकार अधिनियमाअंतर्गत अर्ज केला आहे आणि मुदत संपली आहे ळ") == "mr"
    assert detect_language("12 34") == "unknown"


def test_chunking_respects_size_and_sentences():
    text = ". ".join(f"Sentence number {i} about the appeal" for i in range(200)) + "."
    chunks = chunk_text(text, chunk_size=400, overlap=50)
    assert len(chunks) > 5
    assert all(len(c) <= 400 for c in chunks)
    marathi = "। ".join(f"वाक्य क्रमांक {i} अपील संदर्भात आहे" for i in range(100))
    assert all(len(c) <= 400 for c in chunk_text(marathi, 400, 50))


def test_detects_garbled_devanagari_text_layer():
    from app.processing.cleaning import looks_garbled

    garbled = "महाारााष्ट्रट शाासन रााजपत्र असाधाारण भााग चाार-अ वर्षष १२ अंंक ७२ शुुक्रवार प्रााधि�कृृत प्रकााशन" * 2
    clean = "महाराष्ट्र शासन राजपत्र असाधारण भाग चार-अ वर्ष १२ अंक ७२ शुक्रवार प्राधिकृत प्रकाशन" * 2
    assert looks_garbled(garbled) and not looks_garbled(clean)
    assert not looks_garbled("Plain English text without any Devanagari at all, just a long sentence." * 3)
