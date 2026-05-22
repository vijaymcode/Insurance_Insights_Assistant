import sqlite3
import random
from datetime import date, timedelta
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "insurance.db")

STATES_REGIONS = {
    "CA": "West", "WA": "West", "OR": "West",
    "AZ": "Southwest", "NM": "Southwest",
    "CO": "Mountain", "UT": "Mountain",
    "TX": "South", "OK": "South", "LA": "South",
    "FL": "Southeast", "GA": "Southeast", "NC": "Southeast", "SC": "Southeast",
    "NY": "Northeast", "MA": "Northeast", "CT": "Northeast", "NJ": "Northeast",
    "IL": "Midwest", "OH": "Midwest", "MI": "Midwest", "MN": "Midwest",
}

FIRST_NAMES = [
    "James","Mary","John","Patricia","Robert","Jennifer","Michael","Linda","William","Barbara",
    "David","Susan","Richard","Jessica","Joseph","Sarah","Thomas","Karen","Charles","Lisa",
    "Christopher","Nancy","Daniel","Betty","Matthew","Margaret","Anthony","Sandra","Mark","Ashley",
    "Donald","Dorothy","Steven","Kimberly","Paul","Emily","Andrew","Donna","Joshua","Michelle",
    "Kenneth","Carol","Kevin","Amanda","Brian","Melissa","George","Deborah","Timothy","Stephanie",
]

LAST_NAMES = [
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez",
    "Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin",
    "Lee","Perez","Thompson","White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson",
    "Walker","Young","Allen","King","Wright","Scott","Torres","Nguyen","Hill","Flores",
    "Green","Adams","Nelson","Baker","Hall","Rivera","Campbell","Mitchell","Carter","Roberts",
]

CLAIM_DESCRIPTIONS = {
    "auto": [
        "Rear-end collision at intersection",
        "Hail damage to vehicle",
        "Windshield crack from road debris",
        "Side-swipe in parking lot",
        "Theft of catalytic converter",
        "Flood damage to engine",
        "Single-vehicle accident on highway",
    ],
    "home": [
        "Roof damage from windstorm",
        "Burst pipe causing water damage",
        "Fire damage to kitchen",
        "Theft of electronics and jewelry",
        "Tree fell on garage",
        "Foundation crack from earthquake",
        "Mold remediation",
    ],
    "health": [
        "Emergency room visit",
        "Scheduled surgery",
        "Physical therapy sessions",
        "Prescription medication",
        "Specialist consultation",
        "Diagnostic imaging",
        "Preventive care visit",
    ],
    "life": [
        "Term life benefit claim",
        "Accidental death benefit",
        "Critical illness rider",
    ],
}


def random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def create_tables(conn: sqlite3.Connection):
    conn.executescript("""
        DROP TABLE IF EXISTS claims;
        DROP TABLE IF EXISTS policies;
        DROP TABLE IF EXISTS customers;

        CREATE TABLE customers (
            customer_id   INTEGER PRIMARY KEY,
            name          TEXT    NOT NULL,
            age           INTEGER,
            gender        TEXT,
            state         TEXT,
            region        TEXT,
            zip_code      TEXT,
            risk_score    REAL,
            customer_since DATE
        );

        CREATE TABLE policies (
            policy_id       INTEGER PRIMARY KEY,
            customer_id     INTEGER REFERENCES customers(customer_id),
            policy_type     TEXT,
            premium         REAL,
            start_date      DATE,
            end_date        DATE,
            status          TEXT,
            region          TEXT,
            coverage_amount REAL
        );

        CREATE TABLE claims (
            claim_id     INTEGER PRIMARY KEY,
            policy_id    INTEGER REFERENCES policies(policy_id),
            customer_id  INTEGER REFERENCES customers(customer_id),
            claim_date   DATE,
            claim_amount REAL,
            claim_status TEXT,
            claim_type   TEXT,
            description  TEXT
        );
    """)
    conn.commit()


def seed_data(conn: sqlite3.Connection):
    random.seed(42)
    states = list(STATES_REGIONS.keys())
    today = date.today()
    three_years_ago = today - timedelta(days=3 * 365)

    # ── Customers ──
    customers = []
    for i in range(1, 101):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        state = random.choice(states)
        region = STATES_REGIONS[state]
        gender = random.choice(["M", "F"])
        age = random.randint(22, 75)
        risk = round(random.uniform(1.0, 10.0), 2)
        since = random_date(three_years_ago, today - timedelta(days=90))
        zip_code = f"{random.randint(10000, 99999)}"
        customers.append((i, f"{first} {last}", age, gender, state, region, zip_code, risk, since.isoformat()))

    conn.executemany(
        "INSERT INTO customers VALUES (?,?,?,?,?,?,?,?,?)", customers
    )

    # ── Policies ──
    policy_types = ["auto", "home", "life", "health"]
    premiums = {"auto": (800, 2400), "home": (1200, 3600), "life": (600, 5000), "health": (3000, 8000)}
    coverages = {"auto": (15000, 100000), "home": (200000, 800000), "life": (100000, 1000000), "health": (50000, 500000)}

    policies = []
    pid = 1
    for cust in customers:
        cid, _, _, _, _, region, *_ = cust
        num_policies = random.randint(1, 3)
        for _ in range(num_policies):
            ptype = random.choice(policy_types)
            start = random_date(three_years_ago, today - timedelta(days=30))
            duration = random.choice([365, 730, 365])
            end = start + timedelta(days=duration)
            if end < today:
                status = random.choices(["expired", "cancelled"], weights=[80, 20])[0]
            else:
                status = random.choices(["active", "cancelled"], weights=[90, 10])[0]
            lo, hi = premiums[ptype]
            premium = round(random.uniform(lo, hi), 2)
            clo, chi = coverages[ptype]
            coverage = round(random.uniform(clo, chi), -2)
            policies.append((pid, cid, ptype, premium, start.isoformat(), end.isoformat(), status, region, coverage))
            pid += 1

    conn.executemany(
        "INSERT INTO policies VALUES (?,?,?,?,?,?,?,?,?)", policies
    )

    # ── Claims ──
    statuses = ["pending", "approved", "denied", "settled"]
    status_weights = [15, 40, 15, 30]
    claims = []
    cid = 1
    # ~60% of policies have at least one claim
    claimable = [p for p in policies if p[6] in ("active", "expired")]
    sampled = random.sample(claimable, min(len(claimable), int(len(claimable) * 0.6)))
    for pol in sampled:
        pol_id, cust_id, ptype, premium, start_str, end_str, status, region, coverage = pol
        start_date = date.fromisoformat(start_str)
        end_date = date.fromisoformat(end_str)
        num_claims = random.choices([1, 2, 3], weights=[70, 20, 10])[0]
        for _ in range(num_claims):
            claim_date = random_date(start_date, min(end_date, today))
            lo_pct, hi_pct = 0.01, 0.40
            amount = round(random.uniform(coverage * lo_pct, coverage * hi_pct), 2)
            amount = min(amount, coverage)
            claim_status = random.choices(statuses, weights=status_weights)[0]
            desc = random.choice(CLAIM_DESCRIPTIONS[ptype])
            claims.append((cid, pol_id, cust_id, claim_date.isoformat(), amount, claim_status, ptype, desc))
            cid += 1

    conn.executemany(
        "INSERT INTO claims VALUES (?,?,?,?,?,?,?,?)", claims
    )
    conn.commit()
    print(f"Seeded: {len(customers)} customers, {len(policies)} policies, {len(claims)} claims")


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    create_tables(conn)
    seed_data(conn)
    conn.close()
    print(f"Database ready at: {DB_PATH}")


if __name__ == "__main__":
    init_db()
