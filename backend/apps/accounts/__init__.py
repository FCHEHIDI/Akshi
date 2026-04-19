"""
Accounts app — Organisation, User, Membership, Domain, APIKey models.

This app lives in the SHARED_APPS list and its tables are created in the
public PostgreSQL schema (shared across all tenants).
"""

default_app_config = "apps.accounts.apps.AccountsConfig"
