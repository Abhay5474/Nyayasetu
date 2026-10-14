"""English / Marathi wording for each draft, built as neutral blocks that render.py turns into PDF or Word.

Wording follows the official Maharashtra forms (Annexure "A" and "B" of the Maharashtra Right to Information Rules, 2026) and
cites the provision each paragraph rests on. Marathi text should be read by a Marathi speaker before it is relied on.
"""
from __future__ import annotations

import datetime as dt
from decimal import Decimal

from app.drafts.schemas import Block, DraftDocument, FeePaymentReply, FirstAppeal, RtiApplication

_DEV = str.maketrans("0123456789", "०१२३४५६७८९")
APPEAL_DAYS = 30  # section 19(1)
REPLY_DAYS = 30  # section 7(1)
WORD_LIMIT = 150  # Maharashtra rules 2026, rule 3(b): ordinarily one subject, not more than 150 words
RATE_PER_PAGE = Decimal("2")  # Maharashtra rules 2026, rule 4: Rs. 2 per page (A4/A3)


def _num(s: str, lang: str) -> str:
    return s.translate(_DEV) if lang == "mr" else s


def _date(d: dt.date, lang: str) -> str:
    return _num(d.strftime("%d/%m/%Y"), lang)


def _money(x: Decimal | int, lang: str) -> str:
    x = Decimal(x)
    s = f"{x:.0f}" if x == x.to_integral() else f"{x:.2f}"
    return _num(s, lang)


def _t(lang: str, en: str, mr: str) -> str:
    return mr if lang == "mr" else en


def _numbered(items: list[str], lang: str) -> list[str]:
    return [f"{_num(str(i), lang)}. {text}" for i, text in enumerate(items, start=1)]


def _contact(d) -> str:
    return " / ".join(x for x in (d.phone, d.email) if x)


def _closing(d, lang: str, name_label: str, salutation: str | None = None) -> list[Block]:
    out = [Block(type="spacer")]
    out.append(Block(type="para", text=f"{_t(lang, 'Place', 'ठिकाण')} : {d.place}"))
    out.append(Block(type="para", text=f"{_t(lang, 'Date', 'दिनांक')} : {_date(d.date, lang)}"))
    out.append(Block(type="signature", text=(salutation + "\n" if salutation else "") + f"{name_label}\n\n{d.full_name}"))
    return out


# ----------------------------------------------------------------------------- fee wording
_FEE = {
    "court_fee_stamp": ("by court fee stamp (affixed above)", "न्यायालय फी मुद्रांकाद्वारे (वर चिकटवलेले)"),
    "cash": ("in cash against receipt no. {ref}", "रोख रकमेने (पावती क्र. {ref})"),
    "demand_draft": ("by demand draft no. {ref}", "धनाकर्षाने (क्र. {ref})"),
    "banker_cheque": ("by banker's cheque no. {ref}", "बँकर्स चेकने (क्र. {ref})"),
    "online": ("online (transaction no. {ref})", "ऑनलाइन (व्यवहार क्र. {ref})"),
}


def _fee_phrase(mode: str, ref: str | None, lang: str) -> str:
    en, mr = _FEE[mode]
    return _t(lang, en, mr).format(ref=ref or "-")


# ----------------------------------------------------------------------------- RTI application (Annexure "A")
def rti_application(d: RtiApplication) -> DraftDocument:
    L = d.language
    blocks: list[Block] = []
    if d.fee_mode == "court_fee_stamp" and not d.below_poverty_line:
        blocks.append(Block(type="box", text=_t(L, "Affix here Court Fee Stamp of Rs. 10/-", "येथे १० रु. चा न्यायालय फी मुद्रांक चिकटवावा")))
    blocks.append(Block(type="subtitle", text=_t(L, 'Annexure "A" [See rule 3 (a), Maharashtra Right to Information Rules, 2026]',
                                                 'जोडपत्र “अ” [महाराष्ट्र माहितीचा अधिकार नियम, २०२६ चा नियम ३ (क) पहा]')))
    blocks.append(Block(type="title", text=_t(L, "Application for obtaining information under the Right to Information Act, 2005",
                                              "माहितीचा अधिकार अधिनियम, २००५ अन्वये माहिती मिळविण्यासाठीचा अर्ज")))
    blocks.append(Block(type="para", text=_t(L, "To,\nThe State Public Information Officer,\n", "प्रति,\nराज्य जन माहिती अधिकारी,\n") + d.authority))
    delivery = _t(L, "By post", "टपालाद्वारे") if d.delivery == "post" else _t(L, "In person", "व्यक्तिशः")
    post_mode = {"ordinary": _t(L, "Ordinary", "सर्वसाधारण"), "registered": _t(L, "Registered", "नोंदणीकृत"), "speed": _t(L, "Speed", "शीघ्र")}.get(d.post_mode or "", _t(L, "Not applicable", "लागू नाही"))
    bpl = (_t(L, "Yes - photocopy of proof attached", "होय - पुराव्याची छायांकित प्रत जोडली आहे")
           + (f" ({_t(L, 'card no.', 'कार्ड क्र.')} {d.bpl_card_no})" if d.bpl_card_no else "")) if d.below_poverty_line else _t(L, "No", "नाही")
    contact = _contact(d)
    rows = [
        (_t(L, "(1) Full name of the applicant", "(१) अर्जदाराचे संपूर्ण नाव"), d.full_name),
        (_t(L, "(2) Address", "(२) पत्ता"), d.address + (f"\n{_t(L, 'Contact', 'संपर्क')}: {contact}" if contact else "")),
        (_t(L, "(3) Particulars of information required", "(३) हव्या असलेल्या माहितीचा तपशील"), ""),
        (_t(L, "(i) Subject matter of information", "(एक) माहितीचा विषय"), d.subject),
        (_t(L, "(ii) The period to which the information relates", "(दोन) ज्या कालावधी संबंधात माहिती हवी तो कालावधी"), d.period or _t(L, "Not specified", "नमूद नाही")),
        (_t(L, "(iii) Description of the information required", "(तीन) हव्या असलेल्या माहितीचे वर्णन"), "\n".join(_numbered(d.items, L))),
        (_t(L, "(iv) Whether information is required by post or in person", "(चार) माहिती टपालाद्वारे हवी आहे की व्यक्तिशः"), delivery),
        (_t(L, "(v) In case by post (Ordinary, Registered or Speed)", "(पाच) टपालाद्वारे हवी असल्यास (सर्वसाधारण, नोंदणीकृत किंवा शीघ्र)"), post_mode),
        (_t(L, "(4) Whether the applicant is below poverty line", "(४) अर्जदार दारिद्र्यरेषेखालील आहे किंवा कसे"), bpl),
    ]
    blocks.append(Block(type="rows", rows=rows))
    if d.delivery == "post":
        blocks.append(Block(type="para", text=_t(L, "The actual postal charges shall be included in addition to the fee.", "प्रत्यक्ष टपालखर्च अतिरिक्त फीमध्ये समाविष्ट करण्यात येईल.")))
    if d.below_poverty_line:
        blocks.append(Block(type="para", text=_t(
            L, "As I am below the poverty line, no fee may be charged from me (proviso to Section 7(5) of the Right to Information Act, 2005). "
               "A photocopy of the proof is attached.",
            "मी दारिद्र्यरेषेखालील असल्याने माहितीचा अधिकार अधिनियम, २००५ च्या कलम ७(५) च्या परंतुकानुसार माझ्याकडून कोणतेही शुल्क आकारले जाऊ नये. "
            "पुराव्याची छायांकित प्रत जोडली आहे.")))
    else:
        blocks.append(Block(type="para", text=_t(
            L, f"The application fee of Rs. {_money(10, L)}/- has been paid {_fee_phrase(d.fee_mode, d.fee_reference, L)}.",
            f"अर्ज शुल्क म्हणून रुपये {_money(10, L)}/- {_fee_phrase(d.fee_mode, d.fee_reference, L)} भरले आहे.")))
    blocks.append(Block(type="para", text=_t(
        L, "Kindly provide the above information within thirty days of receipt of this application, as required by Section 7(1) of the Act.",
        "कृपया वरील माहिती हा अर्ज मिळाल्यापासून ३० दिवसांच्या आत, अधिनियमाच्या कलम ७(१) नुसार, उपलब्ध करून द्यावी.")))
    blocks += _closing(d, L, _t(L, "Signature of the Applicant", "अर्जदाराची सही"))

    words = len(" ".join([d.subject, d.period or "", *d.items]).split())
    warnings = []
    if words > WORD_LIMIT:
        warnings.append(_t(L, f"Your request is about {words} words. The Maharashtra Rules (rule 3(b)) say an application should ordinarily cover one "
                              f"subject and stay within {WORD_LIMIT} words; a longer one may be rejected or split. Shorten it or file separate applications.",
                           f"तुमची विनंती सुमारे {_num(str(words), L)} शब्दांची आहे. महाराष्ट्र नियमांनुसार (नियम ३(ख)) अर्ज सामान्यतः एकाच विषयाचा व "
                           f"{_num(str(WORD_LIMIT), L)} शब्दांपर्यंत असावा; मोठा अर्ज नाकारला किंवा विभागला जाऊ शकतो. तो लहान करा किंवा वेगवेगळे अर्ज करा."))
    notes = [
        _t(L, "Ask for one subject per application and be specific about the period and the records you want.", "एका अर्जात एकच विषय घ्या आणि कालावधी व हवे असलेले अभिलेख स्पष्ट लिहा."),
        _t(L, "Keep a photocopy and proof of delivery (acknowledgement / postal receipt). The 30 days start when the PIO receives the application.",
           "अर्जाची छायाप्रत व पोहोच पावती (टपाल पावती / acknowledgement) जपून ठेवा. ३० दिवसांची मुदत माहिती अधिकार्‍याला अर्ज मिळाल्यापासून सुरू होते."),
    ]
    if d.fee_mode == "court_fee_stamp" and not d.below_poverty_line:
        notes.append(_t(L, "Stick a Rs. 10 court fee stamp in the box at the top right and sign across it.", "वरच्या उजव्या चौकटीत १० रुपयांचा न्यायालय फी मुद्रांक चिकटवा."))
    elif not d.below_poverty_line:
        notes.append(_t(L, "Attach a copy of the cash receipt / demand draft / banker's cheque.", "रोख पावती / धनाकर्ष / बँकर्स चेकची प्रत जोडा."))
    return DraftDocument(kind=d.kind, language=L, title=_t(L, "RTI application", "माहिती अधिकार अर्ज"),
                         filename=f"RTI-application-{d.date.isoformat()}", blocks=blocks, warnings=warnings, notes=notes)


# ----------------------------------------------------------------------------- first appeal (Annexure "B")
_GROUNDS = {
    "no_reply": (
        "The State Public Information Officer did not communicate any decision on my application dated {app} within the thirty days "
        "prescribed by Section 7(1) of the Act. This is treated as a refusal under Section 7(2).",
        "राज्य जन माहिती अधिकार्‍याने माझ्या दिनांक {app} च्या अर्जावर अधिनियमाच्या कलम ७(१) मध्ये विहित केलेल्या ३० दिवसांच्या मुदतीत कोणताही निर्णय कळविला नाही. "
        "हे कलम ७(२) अन्वये माहिती नाकारल्याचे मानले जाते."),
    "refused_exemption": (
        "The State Public Information Officer refused the information by relying on an exemption under Section 8 / Section 9 of the Act. "
        "The exemption does not apply to the information I asked for, and the reasons given are not sufficient. Even if an exemption applied "
        "to part of the record, the part that is not exempt had to be supplied under Section 10.",
        "राज्य जन माहिती अधिकार्‍याने अधिनियमाच्या कलम ८ / ९ मधील अपवादाचा आधार घेऊन माहिती नाकारली आहे. मी मागितलेल्या माहितीला हा अपवाद लागू होत नाही व दिलेली कारणे पुरेशी नाहीत. "
        "अपवाद अभिलेखाच्या काही भागाला लागू असला तरी, जो भाग अपवादित नाही तो कलम १० नुसार देणे आवश्यक होते."),
    "incomplete": (
        "The information supplied is incomplete and does not correspond to what I asked for.",
        "देण्यात आलेली माहिती अपूर्ण असून मी मागितलेल्या माहितीशी जुळत नाही."),
    "wrong_fee": (
        "The fee demanded is excessive and not as per the prescribed rates, and the calculation of the fee was not given as required by Section 7(3)(a).",
        "मागण्यात आलेली फी जास्त असून विहित दरांनुसार नाही, तसेच कलम ७(३)(क) नुसार तिच्या गणनेचा तपशील देण्यात आलेला नाही."),
    "misleading": (
        "The information supplied is incorrect or misleading.",
        "देण्यात आलेली माहिती चुकीची किंवा दिशाभूल करणारी आहे."),
}


def appeal_last_date(d: FirstAppeal) -> dt.date:
    """Section 19(1): 30 days from receipt of the decision, or - if none came - 30 days after the PIO's own 30 days ran out."""
    if d.order_received_date:
        return d.order_received_date + dt.timedelta(days=APPEAL_DAYS)
    return d.application_date + dt.timedelta(days=REPLY_DAYS + APPEAL_DAYS)


def first_appeal(d: FirstAppeal, today: dt.date | None = None) -> DraftDocument:
    L, today = d.language, today or dt.date.today()
    last = appeal_last_date(d)
    late = today > last
    blocks: list[Block] = []
    if d.fee_mode == "court_fee_stamp":
        blocks.append(Block(type="box", text=_t(L, "Affix here Court Fee Stamp of Rs. 20/-", "येथे २० रु. चा न्यायालय फी मुद्रांक चिकटवावा")))
    blocks.append(Block(type="subtitle", text=_t(L, 'Annexure "B" [See rule 5 (1), Maharashtra Right to Information Rules, 2026]', "जोडपत्र “ब” [नियम ५ (१) पहा]")))
    blocks.append(Block(type="title", text=_t(L, "Appeal under Section 19(1) of the Right to Information Act, 2005", "माहितीचा अधिकार अधिनियम, २००५ याच्या कलम १९(१) खालील अपील")))
    blocks.append(Block(type="para", text=_t(L, "From:\n", "प्रेषक :\n") + f"{d.full_name}\n{d.address}"))
    blocks.append(Block(type="para", text=_t(L, "To,\n", "प्रति,\n") + d.appellate_authority))
    received = (_date(d.order_received_date, L) if d.order_received_date else
                _t(L, "No decision was received within 30 days of the application", "अर्जानंतर ३० दिवसांत कोणताही निर्णय मिळाला नाही"))
    contact = _contact(d)
    rows = [
        (_t(L, "(1) Full name of the Appellant", "(१) अपीलकाराचे संपूर्ण नाव"), d.full_name),
        (_t(L, "(2) Address", "(२) पत्ता"), d.address + (f"\n{_t(L, 'Contact', 'संपर्क')}: {contact}" if contact else "")),
        (_t(L, "(3) Particulars of the State Public Information Officer", "(३) राज्य जन माहिती अधिकार्‍याचा तपशील"), d.pio_details),
        (_t(L, "(4) Date of receipt of the order appealed against (if an order was passed)", "(४) ज्या आदेशाविरुद्ध अपील केले आहे तो आदेश मिळाल्याचा दिनांक (आदेश काढला असल्यास)"),
         received + (f" ({_t(L, 'Ref', 'संदर्भ')} {d.order_ref})" if d.order_ref else "")),
        (_t(L, "(5) Last date for filing the appeal", "(५) अपील दाखल करण्याचा अंतिम दिनांक"), _date(last, L)),
        (_t(L, "(6) The grounds for appeal", "(६) अपीलाची कारणे"), _t(L, "As stated below", "खाली नमूद केल्याप्रमाणे")),
        (_t(L, "(7) Particulars of information", "(७) माहितीचा तपशील"), ""),
        (_t(L, "(i) Nature and subject matter of the information required", "(एक) हव्या असलेल्या माहितीचे स्वरूप आणि विषय"), d.info_subject),
        (_t(L, "(ii) Name of the Office or Department to which the information relates", "(दोन) माहिती ज्या कार्यालयाशी किंवा विभागाशी संबंधित आहे त्याचे नाव"), d.info_office),
    ]
    blocks.append(Block(type="rows", rows=rows))
    ref = f" ({_t(L, 'ref.', 'संदर्भ')} {d.application_ref})" if d.application_ref else ""
    blocks.append(Block(type="para", bold=True, text=_t(L, "Facts", "वस्तुस्थिती")))
    blocks.append(Block(type="para", text=_t(
        L, f"I applied to the State Public Information Officer under Section 6(1) of the Right to Information Act, 2005 on {_date(d.application_date, L)}{ref} for the information described above."
           + (f" The Public Information Officer's decision was received by me on {_date(d.order_received_date, L)}." if d.order_received_date else " I have received no decision on it."),
        f"मी दिनांक {_date(d.application_date, L)}{ref} रोजी माहितीचा अधिकार अधिनियम, २००५ च्या कलम ६(१) अन्वये वर नमूद केलेल्या माहितीसाठी राज्य जन माहिती अधिकार्‍याकडे अर्ज केला होता."
        + (f" माहिती अधिकार्‍याचा निर्णय मला दिनांक {_date(d.order_received_date, L)} रोजी मिळाला." if d.order_received_date else " त्यावर मला कोणताही निर्णय मिळालेला नाही."))))
    grounds = [(_t(L, *_GROUNDS[g])).format(app=_date(d.application_date, L)) for g in d.grounds if g != "other"]
    if "other" in d.grounds and d.grounds_other:
        grounds.append(d.grounds_other)
    blocks.append(Block(type="para", bold=True, text=_t(L, "Grounds of appeal", "अपीलाची कारणे")))
    blocks.append(Block(type="numbered", items=_numbered(grounds, L)))
    if late:
        blocks.append(Block(type="para", bold=True, text=_t(L, "Request to condone delay", "विलंब माफ करण्याची विनंती")))
        blocks.append(Block(type="para", text=_t(
            L, "This appeal is filed after the thirty days allowed by Section 19(1). The delay was caused by: "
               + (d.delay_reason or "[state the reason]") + " Under the proviso to Section 19(1), I request that the appeal be admitted, as I was prevented by sufficient cause from filing it in time.",
            "हे अपील कलम १९(१) अन्वये दिलेल्या ३० दिवसांच्या मुदतीनंतर दाखल करीत आहे. विलंबाचे कारण: "
            + (d.delay_reason or "[कारण लिहा]") + " कलम १९(१) च्या परंतुकानुसार, मला पुरेशा कारणास्तव मुदतीत अपील करता आले नाही, म्हणून अपील दाखल करून घेण्याची विनंती आहे.")))
    prayer = [_t(L, "To direct the State Public Information Officer to supply the complete information I asked for.", "राज्य जन माहिती अधिकार्‍यास मी मागितलेली संपूर्ण माहिती देण्याचे निर्देश द्यावेत.")]
    if "no_reply" in d.grounds:
        prayer.append(_t(L, "To direct that the information be supplied free of charge, as the time limit was not met (Section 7(6)).", "मुदतीचे पालन न झाल्याने ही माहिती कलम ७(६) नुसार विनामूल्य देण्याचे निर्देश द्यावेत."))
    prayer.append(_t(L, "To pass any other order that the Appellate Authority considers just.", "अपील प्राधिकार्‍यास योग्य वाटेल असा अन्य आदेश द्यावा."))
    blocks.append(Block(type="para", bold=True, text=_t(L, "Prayer", "विनंती")))
    blocks.append(Block(type="numbered", items=_numbered(prayer, L)))
    blocks.append(Block(type="para", text=_t(
        L, f"The appeal fee of Rs. {_money(20, L)}/- has been paid {_fee_phrase(d.fee_mode, d.fee_reference, L)}.",
        f"अपील शुल्क म्हणून रुपये {_money(20, L)}/- {_fee_phrase(d.fee_mode, d.fee_reference, L)} भरले आहे.")))
    blocks += _closing(d, L, _t(L, "Signature of the Appellant", "अपीलकाराची सही"))

    warnings: list[str] = []
    if not d.order_received_date and today <= d.application_date + dt.timedelta(days=REPLY_DAYS):
        warnings.append(_t(L, f"The PIO still has time to reply (until {_date(d.application_date + dt.timedelta(days=REPLY_DAYS), L)}). An appeal for no reply can be filed only after that date.",
                           f"माहिती अधिकार्‍याला उत्तर देण्यास अजून वेळ आहे ({_date(d.application_date + dt.timedelta(days=REPLY_DAYS), L)} पर्यंत). उत्तर न मिळाल्याचे अपील त्या तारखेनंतरच करता येते."))
    if late and not d.delay_reason:
        warnings.append(_t(L, f"The 30-day period appears to have ended on {_date(last, L)}. You can still file, but explain the reason for the delay in the request included in the draft.",
                           f"३० दिवसांची मुदत {_date(last, L)} रोजी संपलेली दिसते. तरीही अपील करता येते, पण मसुद्यातील विलंब माफीच्या विनंतीमध्ये विलंबाचे कारण लिहा."))
    if not d.order_received_date and "no_reply" not in d.grounds:
        warnings.append(_t(L, "You said no decision was received, but did not select the ground 'no reply'. Consider adding it.", "निर्णय मिळाला नाही असे तुम्ही सांगितले, पण 'उत्तर नाही' हे कारण निवडलेले नाही. ते जोडण्याचा विचार करा."))
    if d.order_received_date and "no_reply" in d.grounds:
        warnings.append(_t(L, "You entered a received decision but also selected 'no reply'. Remove one of them.", "निर्णय मिळाल्याची तारीख दिली आहे, तरीही 'उत्तर नाही' हे कारण निवडले आहे. एक काढा."))
    notes = [
        _t(L, "Attach copies of your original application, the PIO's reply (if any) and proof of delivery.", "तुमच्या मूळ अर्जाची प्रत, माहिती अधिकार्‍याचे उत्तर (असल्यास) व पोहोच पावतीची प्रत जोडा."),
        _t(L, "Address it to an officer senior to the PIO in the same public authority (the First Appellate Authority named in the PIO's reply or on the office notice board).",
           "तो त्याच सार्वजनिक प्राधिकरणातील माहिती अधिकार्‍यापेक्षा वरिष्ठ अधिकार्‍याकडे (प्रथम अपील प्राधिकारी) पाठवा; त्याचे नाव उत्तरात किंवा कार्यालयाच्या सूचना फलकावर असते."),
        _t(L, "A penalty on the PIO under Section 20 can be asked for only in a second appeal or complaint to the Information Commission, not here.",
           "माहिती अधिकार्‍यावरील दंड (कलम २०) फक्त माहिती आयोगाकडील द्वितीय अपील / तक्रारीत मागता येतो, येथे नाही."),
    ]
    if d.fee_mode == "court_fee_stamp":
        notes.append(_t(L, "Stick a Rs. 20 court fee stamp in the box at the top right.", "वरच्या उजव्या चौकटीत २० रुपयांचा न्यायालय फी मुद्रांक चिकटवा."))
    return DraftDocument(kind=d.kind, language=L, title=_t(L, "First appeal", "प्रथम अपील"), filename=f"RTI-first-appeal-{d.date.isoformat()}",
                         blocks=blocks, warnings=warnings, notes=notes, last_date=last)


# ----------------------------------------------------------------------------- reply to a demand for further fee (section 7(3))
def fee_payment_reply(d: FeePaymentReply) -> DraftDocument:
    L = d.language
    ref = d.pio_letter_ref or "-"
    blocks = [
        Block(type="title", text=_t(L, "Intimation of payment of further fee", "अतिरिक्त शुल्क भरल्याबाबत कळविण्याचे पत्र")),
        Block(type="para", text=_t(L, "To,\nThe State Public Information Officer,\n", "प्रति,\nराज्य जन माहिती अधिकारी,\n") + d.pio_office),
        Block(type="para", bold=True, text=_t(
            L, f"Subject: Right to Information Act, 2005 - my application dated {_date(d.application_date, L)}"
               + (f" ({d.application_ref})" if d.application_ref else "") + " - payment of further fee",
            f"विषय : माहितीचा अधिकार अधिनियम, २००५ - माझा दिनांक {_date(d.application_date, L)} चा अर्ज"
            + (f" ({d.application_ref})" if d.application_ref else "") + " - अतिरिक्त शुल्क भरणा")),
        Block(type="para", text=_t(L, f"Reference: Your letter no. {ref} dated {_date(d.pio_letter_date, L)}.", f"संदर्भ : आपले पत्र क्र. {ref} दिनांक {_date(d.pio_letter_date, L)}.")),
        Block(type="para", text=_t(L, "Sir / Madam,", "महोदय / महोदया,")),
        Block(type="para", text=_t(
            L, f"By the above letter you asked me to pay Rs. {_money(d.amount_demanded, L)}/- as further fee for providing the information. I have paid "
               f"Rs. {_money(d.amount_paid, L)}/- on {_date(d.payment_date, L)} {_fee_phrase(d.payment_mode, d.payment_reference, L)}. A copy of the proof of payment is attached.",
            f"वरील पत्राद्वारे आपण माहिती देण्यासाठी रुपये {_money(d.amount_demanded, L)}/- इतके अतिरिक्त शुल्क भरण्यास कळविले होते. मी दिनांक {_date(d.payment_date, L)} रोजी "
            f"रुपये {_money(d.amount_paid, L)}/- {_fee_phrase(d.payment_mode, d.payment_reference, L)} भरले आहेत. भरणा पुराव्याची प्रत सोबत जोडली आहे.")),
    ]
    warnings: list[str] = []
    expected = (RATE_PER_PAGE * d.pages) if d.pages else None
    if expected is not None and expected != d.amount_demanded:
        blocks.append(Block(type="para", text=_t(
            L, f"At the prescribed rate of Rs. {_money(RATE_PER_PAGE, L)} per page, {_num(str(d.pages), L)} pages would cost Rs. {_money(expected, L)}/-, whereas Rs. {_money(d.amount_demanded, L)}/- was demanded. "
               "Please give the calculation of the fee as required by Section 7(3)(a) and correct the amount if it is wrong. I reserve my right to seek a review of the fee under Section 7(3)(b).",
            f"विहित दर प्रति पान रुपये {_money(RATE_PER_PAGE, L)} नुसार {_num(str(d.pages), L)} पानांसाठी रुपये {_money(expected, L)}/- शुल्क होते, तर आपण रुपये {_money(d.amount_demanded, L)}/- मागितले आहेत. "
            "कृपया कलम ७(३)(क) नुसार शुल्काची गणना कळवावी व रक्कम चुकीची असल्यास दुरुस्त करावी. कलम ७(३)(ख) नुसार शुल्काचा आढावा घेण्याचा माझा अधिकार मी राखून ठेवत आहे.")))
        warnings.append(_t(L, f"The fee demanded (Rs. {_money(d.amount_demanded, L)}) does not match {d.pages} pages at Rs. 2 per page (Rs. {_money(expected, L)}). The draft asks the PIO to explain.",
                           f"मागितलेले शुल्क (रु. {_money(d.amount_demanded, L)}) हे {_num(str(d.pages), L)} पाने x रु. २ (रु. {_money(expected, L)}) शी जुळत नाही. मसुद्यात माहिती अधिकार्‍यास स्पष्टीकरण मागितले आहे."))
    blocks.append(Block(type="para", text=_t(
        L, "Please now supply the information at the earliest. I understand that, under Section 7(3)(a), the period between the date you intimated the fee and the date it is paid is not counted in the thirty days.",
        "आता कृपया मी मागितलेली माहिती लवकरात लवकर उपलब्ध करून द्यावी. कलम ७(३)(क) नुसार शुल्क कळविल्याचा दिनांक ते शुल्क भरल्याचा दिनांक हा कालावधी ३० दिवसांच्या मोजणीतून वगळला जातो, हे मला माहीत आहे.")))
    blocks.append(Block(type="para", text=_t(L, "Thank you.", "कळावे, धन्यवाद.")))
    blocks += _closing(d, L, _t(L, "Yours faithfully,", "आपला / आपली,"))
    if d.amount_paid < d.amount_demanded:
        warnings.append(_t(L, "You paid less than the amount demanded. The PIO may not release the information until the full amount is paid.", "तुम्ही मागितलेल्या रकमेपेक्षा कमी भरले आहे. पूर्ण रक्कम भरेपर्यंत माहिती अधिकारी माहिती देणार नाही."))
    elif d.amount_paid > d.amount_demanded:
        warnings.append(_t(L, "You paid more than the amount demanded. Check the amount.", "तुम्ही मागितलेल्या रकमेपेक्षा जास्त भरले आहे. रक्कम तपासा."))
    notes = [_t(L, "Attach a copy of the receipt / demand draft / payment proof and keep proof of delivery.", "भरणा पावती / धनाकर्ष / पुराव्याची प्रत जोडा आणि पोहोच पावती जपून ठेवा."),
             _t(L, "Send it to the PIO who wrote to you, not to the appellate authority.", "हे पत्र तुम्हाला लिहिणार्‍या माहिती अधिकार्‍याकडे पाठवा, अपील प्राधिकार्‍याकडे नाही.")]
    return DraftDocument(kind=d.kind, language=L, title=_t(L, "Fee payment reply", "शुल्क भरणा पत्र"), filename=f"RTI-fee-payment-{d.date.isoformat()}",
                         blocks=blocks, warnings=warnings, notes=notes)


def build(draft) -> DraftDocument:
    return {"rti_application": rti_application, "first_appeal": first_appeal, "fee_payment_reply": fee_payment_reply}[draft.kind](draft)
