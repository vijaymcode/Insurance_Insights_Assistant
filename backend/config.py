import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
DB_PATH = os.path.join(os.path.dirname(__file__), "database", "insurance.db")

ALLOWED_TABLES = {"customers", "policies", "claims"}
MAX_ROWS = 500

TABLE_SCHEMA = {
    "customers": {
        "description": "Insurance customers / policyholders",
        "columns": {
            "customer_id":    "INTEGER PRIMARY KEY",
            "name":           "TEXT - full name",
            "age":            "INTEGER",
            "gender":         "TEXT - 'M' or 'F'",
            "state":          "TEXT - US state abbreviation (e.g. 'CA')",
            "region":         "TEXT - 'West','Southwest','Mountain','South','Southeast','Northeast','Midwest'",
            "zip_code":       "TEXT",
            "risk_score":     "REAL - 1.0 (low risk) to 10.0 (high risk)",
            "customer_since": "DATE",
        },
    },
    "policies": {
        "description": "Insurance policies held by customers",
        "columns": {
            "policy_id":       "INTEGER PRIMARY KEY",
            "customer_id":     "INTEGER - FK to customers",
            "policy_type":     "TEXT - 'auto','home','life','health'",
            "premium":         "REAL - annual premium in USD",
            "start_date":      "DATE",
            "end_date":        "DATE",
            "status":          "TEXT - 'active','expired','cancelled'",
            "region":          "TEXT - same as customer region",
            "coverage_amount": "REAL - maximum coverage in USD",
        },
    },
    "claims": {
        "description": "Claims filed against policies",
        "columns": {
            "claim_id":     "INTEGER PRIMARY KEY",
            "policy_id":    "INTEGER - FK to policies",
            "customer_id":  "INTEGER - FK to customers",
            "claim_date":   "DATE",
            "claim_amount": "REAL - amount claimed in USD",
            "claim_status": "TEXT - 'pending','approved','denied','settled'",
            "claim_type":   "TEXT - matches policy_type: 'auto','home','life','health'",
            "description":  "TEXT - free-text description",
        },
    },
}

DOMAIN_GLOSSARY = """
Insurance domain terms used in this dataset:
- loss_ratio: total claim_amount / total premium (lower is better for the insurer)
- policy_in_force / active policy: a policy with status = 'active'
- earned_premium: premium for the period the policy was active
- combined_ratio: loss ratio + expense ratio (simplified here as loss ratio)
- risk_score: customer's risk level, 1 = safest, 10 = highest risk
- underwriting: the process of evaluating and pricing risk
- settlement: a claim that has been resolved and paid (claim_status = 'settled')
"""
