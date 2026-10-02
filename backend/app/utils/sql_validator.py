"""
SQL validation and safety enforcement.

ALLOWS: SELECT, WITH, aggregations, JOIN, GROUP BY, ORDER BY, WHERE, HAVING, LIMIT
BLOCKS: DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE, CREATE, GRANT, REVOKE

All LLM-generated SQL must pass through validate_sql() before execution.
"""

import re
from dataclasses import dataclass
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)

# Statements that are absolutely forbidden
BLOCKED_KEYWORDS = [
    r"\bDROP\b",
    r"\bDELETE\b",
    r"\bUPDATE\b",
    r"\bINSERT\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bCREATE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
    r"\bCALL\b",
    r"\bCOPY\b",
    r"\bIMPORT\b",
    r"\bSET\s+",
    r"\bRESET\b",
    r"\bBEGIN\b",
    r"\bCOMMIT\b",
    r"\bROLLBACK\b",
    r"\bSAVEPOINT\b",
    r"\bLOCK\b",
    r"\bUNLOCK\b",
    r"\bVACUUM\b",
    r"\bANALYZE\b",
    r"\bEXPLAIN\b",
    r"\bLISTEN\b",
    r"\bNOTIFY\b",
    r"\bLOAD\b",
    r"\bREINDEX\b",
]

# Known valid tables in our schema
VALID_TABLES = {
    "users", "customers", "products", "orders", "order_items",
    "employees", "expenses", "marketing_campaigns", "support_tickets",
}

# SQL injection patterns
INJECTION_PATTERNS = [
    r";\s*\w",          # Multiple statements
    r"--",              # SQL comment (can hide malicious code)
    r"/\*",             # Block comment start
    r"\*/",             # Block comment end
    r"xp_\w+",         # Extended stored procedures
    r"sp_\w+",         # System stored procedures
    r"0x[0-9a-fA-F]+", # Hex literals (potential injection)
]


@dataclass
class ValidationResult:
    """Result of SQL validation."""
    is_valid: bool
    sql: str
    error: Optional[str] = None
    warnings: list = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

    @property
    def errors(self) -> list:
        return [self.error] if self.error else []

    def __getitem__(self, item):
        if item == "is_valid":
            return self.is_valid
        if item == "sql":
            return self.sql
        if item in ("error", "errors"):
            return self.errors
        if item == "warnings":
            return self.warnings
        raise KeyError(item)

    def get(self, item, default=None):
        try:
            return self[item]
        except KeyError:
            return default

    def __contains__(self, item):
        return item in ("is_valid", "sql", "error", "errors", "warnings")


def validate_sql(sql: str) -> ValidationResult:
    """Validate SQL query for safety.

    Checks:
    1. Query must be a SELECT or WITH (CTE) statement
    2. No blocked keywords (DROP, DELETE, UPDATE, etc.)
    3. No SQL injection patterns
    4. Query length limits
    5. LIMIT clause enforcement

    Args:
        sql: The SQL query string to validate.

    Returns:
        ValidationResult with is_valid flag and any error messages.
    """
    if not sql or not sql.strip():
        return ValidationResult(is_valid=False, sql=sql, error="Empty SQL query")

    # Strip trailing semicolons and whitespace (loop until clean)
    cleaned = sql.strip()
    while cleaned.endswith(";") or (cleaned and cleaned[-1].isspace()):
        cleaned = cleaned.rstrip().rstrip(";")
    cleaned = cleaned.strip()

    if not cleaned:
        return ValidationResult(is_valid=False, sql=sql, error="Empty SQL query")

    warnings = []

    # --- Length check ---
    if len(cleaned) > 5000:
        return ValidationResult(
            is_valid=False, sql=cleaned,
            error="SQL query exceeds maximum length (5000 characters)",
        )

    # --- Strip string literals and double-quoted identifiers before keyword check ---
    # Prevents keywords inside literals (e.g. 'analyze') or quoted aliases from false-positive blocking
    check_sql = re.sub(r"'([^'\\]|\\.|'')*'", " ' ' ", cleaned)
    check_sql = re.sub(r'"([^"\\]|\\.|"")*"', ' " " ', check_sql)
    check_sql = re.sub(r"\bAS\s+ANALYZE\b", " AS _alias_ ", check_sql, flags=re.IGNORECASE)
    upper_check_sql = check_sql.upper()
    upper_cleaned = cleaned.upper()

    # --- Check blocked keywords ---
    for pattern in BLOCKED_KEYWORDS:
        if re.search(pattern, upper_check_sql, re.IGNORECASE):
            keyword = re.search(pattern, upper_check_sql, re.IGNORECASE).group().strip()
            return ValidationResult(
                is_valid=False, sql=cleaned,
                error=f"Blocked SQL keyword detected: {keyword}",
            )

    # --- Must start with SELECT or WITH ---
    if not re.match(r"^\s*(SELECT|WITH)\b", upper_cleaned, re.IGNORECASE):
        return ValidationResult(
            is_valid=False, sql=cleaned,
            error="Only SELECT and WITH (CTE) queries are allowed",
        )

    # --- Check injection patterns ---
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, cleaned):
            return ValidationResult(
                is_valid=False, sql=cleaned,
                error="Potential SQL injection pattern detected",
            )

    # --- Warn if no LIMIT clause ---
    if "LIMIT" not in upper_cleaned:
        warnings.append("No LIMIT clause detected. Consider adding LIMIT to prevent large result sets.")
        # Auto-append LIMIT for safety
        cleaned = cleaned + " LIMIT 1000"

    # --- Check LIMIT value ---
    limit_match = re.search(r"LIMIT\s+(\d+)", upper_cleaned)
    if limit_match:
        limit_val = int(limit_match.group(1))
        if limit_val > 10000:
            cleaned = re.sub(
                r"LIMIT\s+\d+", "LIMIT 10000", cleaned, flags=re.IGNORECASE
            )
            warnings.append(f"LIMIT reduced from {limit_val} to 10000")

    logger.info(f"SQL validation passed (warnings: {len(warnings)})")

    return ValidationResult(
        is_valid=True,
        sql=cleaned,
        warnings=warnings,
    )


def extract_tables_from_sql(sql: str) -> set:
    """Extract table names referenced in a SQL query."""
    # Simple regex extraction of FROM and JOIN targets
    tables = set()
    patterns = [
        r"\bFROM\s+(\w+)",
        r"\bJOIN\s+(\w+)",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, sql, re.IGNORECASE):
            tables.add(match.group(1).lower())
    return tables


def validate_tables(sql: str) -> Optional[str]:
    """Validate that all referenced tables exist in our schema."""
    referenced = extract_tables_from_sql(sql)
    invalid = referenced - VALID_TABLES
    if invalid:
        return f"Unknown table(s): {', '.join(invalid)}. Valid tables: {', '.join(sorted(VALID_TABLES))}"
    return None
