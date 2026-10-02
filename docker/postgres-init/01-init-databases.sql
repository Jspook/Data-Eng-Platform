-- ==============================================================================
-- PostgreSQL Initializer: Database & Schemas Setup
-- Runs automatically on the first container startup via /docker-entrypoint-initdb.d
-- ==============================================================================

-- Create separate metadata database for Apache Airflow
CREATE DATABASE airflow;

-- Ensure required schemas exist in the main Data Warehouse database
\connect ecommerce_dw;

CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

-- Comment on schemas for data catalog documentation
COMMENT ON SCHEMA bronze IS 'Raw unmodified data layer (Landing/Bronze)';
COMMENT ON SCHEMA silver IS 'Cleaned, deduplicated, and standardized data layer';
COMMENT ON SCHEMA gold   IS 'Business-ready dimensional models (Star Schema fact and dimensions)';
