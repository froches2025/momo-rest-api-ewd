import re
import json
import xml.etree.ElementTree as ET
from datetime import datetime

# (transaction_type, regex, who the captured "name" is)
# Order matters: more specific patterns go first.
PATTERNS = [
    ("incoming_money",
     re.compile(r"received (?P<amount>[\d,]+) RWF from (?P<name>[A-Za-z .'-]+?)\s*\(", re.I),
     "sender"),
    ("bank_deposit",
     re.compile(r"deposit of (?P<amount>[\d,]+) RWF", re.I),
     None),
    ("airtime",
     re.compile(r"payment of (?P<amount>[\d,]+) RWF to (?P<name>Airtime)", re.I),
     "receiver"),
    ("payment",
     re.compile(r"payment of (?P<amount>[\d,]+) RWF to (?P<name>[A-Za-z .'-]+?)\s+\d+", re.I),
     "receiver"),
    ("transfer",
     re.compile(r"(?P<amount>[\d,]+) RWF transferred to (?P<name>[A-Za-z .'-]+?)\s*\(", re.I),
     "receiver"),
    ("withdrawal",
     re.compile(r"withdrawn (?P<amount>[\d,]+) RWF", re.I),
     None),
]

BODY_TIME = re.compile(r"(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2})")


def get_timestamp(sms):
    """Use the 'date' attribute (epoch milliseconds); fall back to the time inside the body."""
    raw = sms.get("date")
    if raw and raw.isdigit():
        return datetime.fromtimestamp(int(raw) / 1000).isoformat(timespec="seconds")
    match = BODY_TIME.search(sms.get("body", ""))
    if match:
        return f"{match.group(1)}T{match.group(2)}"
    return None


def parse_sms(body):
    """Return (type, amount, sender, receiver) for one message body."""
    for tx_type, pattern, name_role in PATTERNS:
        m = pattern.search(body)
        if not m:
            continue
        amount = int(m.group("amount").replace(",", ""))
        name = m.groupdict().get("name")
        name = name.strip() if name else None

        if tx_type == "incoming_money":
            return tx_type, amount, name, "account_owner"
        if tx_type == "bank_deposit":
            return tx_type, amount, "bank", "account_owner"
        if tx_type == "withdrawal":
            return tx_type, amount, "account_owner", "agent"
        # payment, airtime, transfer: the owner pays someone
        return tx_type, amount, "account_owner", name
    return "unknown", None, None, None

def parse_file(path="docs/modified_sms_v2-1.xml"):

    tree = ET.parse(path)
    records = []
    for counter, sms in enumerate(tree.getroot().iter("sms"), start=1):
        body = sms.get("body", "")
        tx_type, amount, sender, receiver = parse_sms(body)
        records.append({
            "id": counter,
            "transaction_type": tx_type,
            "amount": amount,
            "sender": sender,
            "receiver": receiver,
            "timestamp": get_timestamp(sms),
        })
    return records


if __name__ == "__main__":
    data = parse_file()
    unknown = sum(1 for r in data if r["transaction_type"] == "unknown")
    print(f"Parsed {len(data)} messages ({unknown} unknown)")
    print(json.dumps(data[:3], indent=2))