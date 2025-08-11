#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
import configparser
import os

def read_odoo_config(config_path='/etc/odoo.conf'):
    """Read Odoo configuration file to get database connection parameters."""
    config = configparser.ConfigParser()
    config.read(config_path)
    
    # Get database connection parameters
    db_name = config.get('options', 'db_name', fallback='odoo')
    db_user = config.get('options', 'db_user', fallback='odoo')
    db_password = config.get('options', 'db_password', fallback='odoo')
    db_host = config.get('options', 'db_host', fallback='localhost')
    db_port = config.get('options', 'db_port', fallback='5432')
    
    return {
        'dbname': db_name,
        'user': db_user,
        'password': db_password,
        'host': db_host,
        'port': db_port
    }

def execute_sql_commands(conn_params):
    """Execute SQL commands to add missing columns."""
    try:
        # Connect to the database
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # SQL commands to add missing columns
        sql_commands = [
            # Add is_hotel column to res_partner table if it doesn't exist
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                            WHERE table_name='res_partner' AND column_name='is_hotel') THEN
                    ALTER TABLE res_partner ADD COLUMN is_hotel boolean DEFAULT false;
                END IF;
            END $$;
            """,
            
            # Add hotel_star_rating column to res_partner table if it doesn't exist
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                            WHERE table_name='res_partner' AND column_name='hotel_star_rating') THEN
                    ALTER TABLE res_partner ADD COLUMN hotel_star_rating character varying;
                END IF;
            END $$;
            """,
            
            # Add is_hotel_accommodation column to product_template table if it doesn't exist
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                            WHERE table_name='product_template' AND column_name='is_hotel_accommodation') THEN
                    ALTER TABLE product_template ADD COLUMN is_hotel_accommodation boolean DEFAULT false;
                END IF;
            END $$;
            """,
            
            # Add hotel_partner_id column to ak_tender_line table if it doesn't exist
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                            WHERE table_name='ak_tender_line' AND column_name='hotel_partner_id') THEN
                    ALTER TABLE ak_tender_line ADD COLUMN hotel_partner_id integer;
                    -- Add foreign key constraint
                    ALTER TABLE ak_tender_line ADD CONSTRAINT ak_tender_line_hotel_partner_id_fkey 
                        FOREIGN KEY (hotel_partner_id) REFERENCES res_partner(id) ON DELETE SET NULL;
                END IF;
            END $$;
            """,
            
            # Add hotel_partner_id column to purchase_order_line table if it doesn't exist
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                            WHERE table_name='purchase_order_line' AND column_name='hotel_partner_id') THEN
                    ALTER TABLE purchase_order_line ADD COLUMN hotel_partner_id integer;
                    -- Add foreign key constraint
                    ALTER TABLE purchase_order_line ADD CONSTRAINT purchase_order_line_hotel_partner_id_fkey 
                        FOREIGN KEY (hotel_partner_id) REFERENCES res_partner(id) ON DELETE SET NULL;
                END IF;
            END $$;
            """
        ]
        
        # Execute each SQL command
        for sql in sql_commands:
            cursor.execute(sql)
            conn.commit()
            
        print("Database schema updated successfully!")
        
    except Exception as e:
        print(f"Error updating database schema: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    # Read Odoo configuration
    conn_params = read_odoo_config()
    
    # Execute SQL commands
    execute_sql_commands(conn_params)