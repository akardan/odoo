-- disable qnb payment provider
UPDATE payment_provider
   SET qnb_merchant_id = NULL,
       qnb_user_code = NULL,
       qnb_user_pass = NULL,
       qnb_merchant_pass = NULL;
