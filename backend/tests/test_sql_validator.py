"""
Tests for SQL validation — the most critical safety component.
"""

import pytest

from app.utils.sql_validator import validate_sql, validate_tables, extract_tables_from_sql


class TestValidateSQL:
    """Test the SQL validation function."""

    # --- Valid queries ---

    def test_simple_select(self):
        result = validate_sql("SELECT * FROM orders LIMIT 10")
        assert result.is_valid is True

    def test_select_with_join(self):
        sql = """
        SELECT o.id, c.name, o.total_amount
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        WHERE o.status = 'completed'
        LIMIT 100
        """
        result = validate_sql(sql)
        assert result.is_valid is True

    def test_aggregation_query(self):
        sql = """
        SELECT region, SUM(total_amount) AS revenue
        FROM orders
        WHERE status != 'cancelled'
        GROUP BY region
        ORDER BY revenue DESC
        LIMIT 10
        """
        result = validate_sql(sql)
        assert result.is_valid is True

    def test_cte_query(self):
        sql = """
        WITH monthly AS (
            SELECT DATE_TRUNC('month', order_date) AS month, SUM(total_amount) AS rev
            FROM orders
            GROUP BY month
        )
        SELECT * FROM monthly ORDER BY month LIMIT 12
        """
        result = validate_sql(sql)
        assert result.is_valid is True

    def test_having_clause(self):
        sql = """
        SELECT customer_id, COUNT(*) AS order_count
        FROM orders
        GROUP BY customer_id
        HAVING COUNT(*) > 5
        LIMIT 50
        """
        result = validate_sql(sql)
        assert result.is_valid is True

    # --- Auto-LIMIT ---

    def test_auto_adds_limit_when_missing(self):
        result = validate_sql("SELECT * FROM orders")
        assert result.is_valid is True
        assert "LIMIT" in result.sql
        assert len(result.warnings) > 0

    def test_reduces_excessive_limit(self):
        result = validate_sql("SELECT * FROM orders LIMIT 99999")
        assert result.is_valid is True
        assert "LIMIT 10000" in result.sql

    # --- Blocked keywords ---

    def test_blocks_drop(self):
        result = validate_sql("DROP TABLE orders")
        assert result.is_valid is False
        assert "DROP" in result.error

    def test_blocks_delete(self):
        result = validate_sql("DELETE FROM orders WHERE id = 1")
        assert result.is_valid is False
        assert "DELETE" in result.error

    def test_blocks_update(self):
        result = validate_sql("UPDATE orders SET total_amount = 0")
        assert result.is_valid is False
        assert "UPDATE" in result.error

    def test_blocks_insert(self):
        result = validate_sql("INSERT INTO orders (customer_id) VALUES (1)")
        assert result.is_valid is False
        assert "INSERT" in result.error

    def test_blocks_alter(self):
        result = validate_sql("ALTER TABLE orders ADD COLUMN hack TEXT")
        assert result.is_valid is False

    def test_blocks_truncate(self):
        result = validate_sql("TRUNCATE orders")
        assert result.is_valid is False

    def test_blocks_grant(self):
        result = validate_sql("GRANT ALL ON orders TO public")
        assert result.is_valid is False

    def test_blocks_create(self):
        result = validate_sql("CREATE TABLE hack (id INT)")
        assert result.is_valid is False

    # --- Injection patterns ---

    def test_blocks_multiple_statements(self):
        result = validate_sql("SELECT 1; DROP TABLE orders")
        assert result.is_valid is False

    def test_blocks_comment_injection(self):
        result = validate_sql("SELECT * FROM orders -- WHERE 1=1")
        assert result.is_valid is False

    # --- Edge cases ---

    def test_empty_query(self):
        result = validate_sql("")
        assert result.is_valid is False

    def test_none_like_query(self):
        result = validate_sql("   ")
        assert result.is_valid is False

    def test_very_long_query(self):
        sql = "SELECT " + ", ".join([f"col{i}" for i in range(1000)]) + " FROM orders LIMIT 1"
        result = validate_sql(sql)
        if len(sql) > 5000:
            assert result.is_valid is False
        else:
            assert result.is_valid is True

    def test_strips_trailing_semicolons(self):
        result = validate_sql("SELECT id FROM orders LIMIT 10;")
        assert result.is_valid is True
        assert not result.sql.endswith(";")

    def test_trailing_semicolon_accepted_with_whitespace(self):
        result = validate_sql("SELECT 1 FROM orders;  ;  \n")
        assert result.is_valid is True
        assert not result.sql.endswith(";")

    def test_blocks_multiple_statements_drop_users(self):
        result = validate_sql("SELECT 1; DROP TABLE users")
        assert result.is_valid is False

    def test_accepts_analyze_in_string_literal(self):
        result = validate_sql("SELECT 'analyze' AS action_type FROM orders")
        assert result.is_valid is True

    def test_blocks_drop_table_x(self):
        result = validate_sql("DROP TABLE x")
        assert result.is_valid is False

    def test_blocks_explain_analyze(self):
        result = validate_sql("EXPLAIN ANALYZE SELECT 1")
        assert result.is_valid is False


class TestExtractTables:
    """Test table name extraction from SQL."""

    def test_simple_from(self):
        tables = extract_tables_from_sql("SELECT * FROM orders")
        assert "orders" in tables

    def test_join(self):
        tables = extract_tables_from_sql(
            "SELECT * FROM orders o JOIN customers c ON o.customer_id = c.id"
        )
        assert "orders" in tables
        assert "customers" in tables

    def test_multiple_joins(self):
        sql = """
        SELECT * FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        JOIN products p ON oi.product_id = p.id
        """
        tables = extract_tables_from_sql(sql)
        assert "order_items" in tables
        assert "orders" in tables
        assert "products" in tables


class TestValidateTables:
    """Test table validation against known schema."""

    def test_valid_tables(self):
        error = validate_tables("SELECT * FROM orders JOIN customers ON 1=1")
        assert error is None

    def test_invalid_table(self):
        error = validate_tables("SELECT * FROM nonexistent_table")
        assert error is not None
        assert "nonexistent_table" in error

    def test_all_valid_tables(self):
        for table in ["users", "customers", "products", "orders", "order_items",
                       "employees", "expenses", "marketing_campaigns", "support_tickets"]:
            error = validate_tables(f"SELECT * FROM {table}")
            assert error is None, f"Table {table} should be valid"
