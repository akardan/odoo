-- Add is_hotel column to res_partner table if it doesn't exist
ALTER TABLE res_partner ADD COLUMN IF NOT EXISTS is_hotel boolean DEFAULT false;

-- Add hotel_star_rating column to res_partner table if it doesn't exist
ALTER TABLE res_partner ADD COLUMN IF NOT EXISTS hotel_star_rating character varying;

-- Add is_hotel_accommodation column to product_template table if it doesn't exist
ALTER TABLE product_template ADD COLUMN IF NOT EXISTS is_hotel_accommodation boolean DEFAULT false;

-- Add hotel_partner_id column to ak_tender_line table if it doesn't exist
ALTER TABLE ak_tender_line ADD COLUMN IF NOT EXISTS hotel_partner_id integer;
ALTER TABLE ak_tender_line ADD CONSTRAINT IF NOT EXISTS ak_tender_line_hotel_partner_id_fkey 
    FOREIGN KEY (hotel_partner_id) REFERENCES res_partner(id) ON DELETE SET NULL;

-- Add hotel_partner_id column to purchase_order_line table if it doesn't exist
ALTER TABLE purchase_order_line ADD COLUMN IF NOT EXISTS hotel_partner_id integer;
ALTER TABLE purchase_order_line ADD CONSTRAINT IF NOT EXISTS purchase_order_line_hotel_partner_id_fkey 
    FOREIGN KEY (hotel_partner_id) REFERENCES res_partner(id) ON DELETE SET NULL;