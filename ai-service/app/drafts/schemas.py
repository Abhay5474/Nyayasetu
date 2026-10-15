from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator

Language = Literal["en", "mr"]
FeeMode = Literal["court_fee_stamp", "cash", "demand_draft", "banker_cheque"]  # Maharashtra RTI Rules 2026, rules 3(a) and 5(1)
Text = Annotated[str, Field(min_length=1, max_length=400)]
LongText = Annotated[str, Field(min_length=1, max_length=2000)]


def _in_future(d: dt.date) -> bool:
    """True for a date after today. One day of slack: the server clock is usually UTC and the user may be several hours ahead."""
    return d > dt.date.today() + dt.timedelta(days=1)


_FUTURE = "is in the future - check that the day and month are the right way round"


def _clean(v):
    """Trim, drop control characters (they break PDF/Word output), keep line breaks."""
    if isinstance(v, str):
        v = "".join(ch for ch in v if ch in "\n\t" or ch >= " ").strip()
    return v


class _Base(BaseModel):
    language: Language = "en"
    full_name: Text
    address: Annotated[str, Field(min_length=3, max_length=500)]
    phone: Optional[Annotated[str, Field(max_length=30)]] = None
    email: Optional[Annotated[str, Field(max_length=120)]] = None
    place: Text
    date: dt.date = Field(default_factory=dt.date.today)

    @model_validator(mode="before")
    @classmethod
    def _strip_all(cls, data):
        """Trim every text value (and list item) before validation; blank optional fields become None."""
        if not isinstance(data, dict):
            return data

        def one(v):
            v = _clean(v)
            return None if v == "" else v

        return {k: ([one(i) for i in v] if isinstance(v, list) else one(v)) for k, v in data.items()}

    @field_validator("date")
    @classmethod
    def _not_far_future(cls, v: dt.date) -> dt.date:
        if v > dt.date.today() + dt.timedelta(days=30):
            raise ValueError("is too far in the future")
        return v


class RtiApplication(_Base):
    """Annexure "A" - application under section 6(1)."""

    kind: Literal["rti_application"]
    authority: LongText  # "State Public Information Officer, <office name and address>"
    subject: Text  # broad subject, e.g. "Road repair works"
    period: Optional[Text] = None
    items: Annotated[list[Annotated[str, Field(min_length=3, max_length=800)]], Field(min_length=1, max_length=10)]
    delivery: Literal["post", "in_person"] = "in_person"
    post_mode: Optional[Literal["ordinary", "registered", "speed"]] = None
    below_poverty_line: bool = False
    bpl_card_no: Optional[Annotated[str, Field(max_length=60)]] = None
    fee_mode: FeeMode = "court_fee_stamp"
    fee_reference: Optional[Annotated[str, Field(max_length=80)]] = None

    @model_validator(mode="after")
    def _check(self):
        if self.delivery == "post" and not self.post_mode:
            self.post_mode = "ordinary"
        if self.delivery != "post":
            self.post_mode = None
        if not self.below_poverty_line and self.fee_mode != "court_fee_stamp" and not self.fee_reference:
            raise ValueError("fee_reference: is required when the fee is paid by cash, demand draft or banker's cheque")
        return self


AppealGround = Literal["no_reply", "refused_exemption", "incomplete", "wrong_fee", "misleading", "other"]


class FirstAppeal(_Base):
    """Annexure "B" - first appeal under section 19(1)."""

    kind: Literal["first_appeal"]
    appellate_authority: LongText  # "First Appellate Authority, <designation and address>"
    pio_details: LongText  # name / designation / office of the PIO who decided the application
    application_date: dt.date  # date the PIO received the RTI application
    application_ref: Optional[Annotated[str, Field(max_length=80)]] = None
    order_received_date: Optional[dt.date] = None  # None => no reply was received
    order_ref: Optional[Annotated[str, Field(max_length=80)]] = None
    grounds: Annotated[list[AppealGround], Field(min_length=1, max_length=6)]
    grounds_other: Optional[Annotated[str, Field(max_length=1500)]] = None
    info_subject: LongText  # nature and subject matter of the information sought
    info_office: Text  # office / department the information relates to
    fee_mode: FeeMode = "court_fee_stamp"
    fee_reference: Optional[Annotated[str, Field(max_length=80)]] = None
    delay_reason: Optional[Annotated[str, Field(max_length=1500)]] = None  # needed when the 30 days have passed

    @model_validator(mode="after")
    def _check(self):
        if _in_future(self.application_date):
            raise ValueError(f"application_date: {_FUTURE}")
        if self.order_received_date and _in_future(self.order_received_date):
            raise ValueError(f"order_received_date: {_FUTURE}")
        if self.order_received_date and self.order_received_date < self.application_date:
            raise ValueError("order_received_date: the decision cannot be dated before your application")
        if "other" in self.grounds and not self.grounds_other:
            raise ValueError("grounds_other: is required when the reason 'another reason' is selected")
        if self.fee_mode != "court_fee_stamp" and not self.fee_reference:
            raise ValueError("fee_reference: is required when the fee is paid by cash, demand draft or banker's cheque")
        return self


class FeePaymentReply(_Base):
    """Reply to a PIO's demand for further fee (section 7(3))."""

    kind: Literal["fee_payment_reply"]
    pio_office: LongText
    pio_letter_ref: Optional[Annotated[str, Field(max_length=80)]] = None
    pio_letter_date: dt.date
    application_date: dt.date
    application_ref: Optional[Annotated[str, Field(max_length=80)]] = None
    amount_demanded: Annotated[Decimal, Field(gt=0, le=10_000_000, max_digits=10, decimal_places=2)]
    pages: Optional[Annotated[int, Field(ge=1, le=100_000)]] = None
    amount_paid: Annotated[Decimal, Field(gt=0, le=10_000_000, max_digits=10, decimal_places=2)]
    payment_mode: Literal["cash", "demand_draft", "banker_cheque", "online"]
    payment_reference: Annotated[str, Field(min_length=1, max_length=80)]
    payment_date: dt.date

    @model_validator(mode="after")
    def _check(self):
        for name in ("application_date", "pio_letter_date", "payment_date"):
            if _in_future(getattr(self, name)):
                raise ValueError(f"{name}: {_FUTURE}")
        if self.pio_letter_date < self.application_date:
            raise ValueError("pio_letter_date: the PIO's letter cannot be dated before your application")
        if self.payment_date < self.pio_letter_date:
            raise ValueError("payment_date: the payment cannot be dated before the PIO's letter")
        return self


DraftRequest = Annotated[Union[RtiApplication, FirstAppeal, FeePaymentReply], Field(discriminator="kind")]


# ----------------------------------------------------------------------------- output
class Block(BaseModel):
    """One piece of the document. type: title | subtitle | box | para | right | rows | numbered | signature | spacer"""

    type: Literal["title", "subtitle", "box", "para", "right", "rows", "numbered", "signature", "spacer"]
    text: str = ""
    rows: list[tuple[str, str]] = Field(default_factory=list)  # for "rows": (label, value) pairs
    items: list[str] = Field(default_factory=list)  # for "numbered"
    bold: bool = False


class DraftDocument(BaseModel):
    kind: str
    language: Language
    title: str
    filename: str
    blocks: list[Block]
    warnings: list[str] = Field(default_factory=list)  # things the person should fix or know before filing
    notes: list[str] = Field(default_factory=list)  # what to attach / how to file
    last_date: Optional[dt.date] = None  # appeals: last date to file without a delay request
