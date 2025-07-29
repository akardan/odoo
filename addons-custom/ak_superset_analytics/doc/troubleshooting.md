# Troubleshooting Guide

This document provides solutions for common issues that might occur when using the Superset Analytics Integration module.

## Connection Issues

If you encounter connection errors like "Connection couldn't be established or was interrupted" or 500 Internal Server Error responses:

1. **Check Odoo Server Status**
   - Ensure your Odoo server is running properly
   - Check the Odoo server logs for any errors
   - Restart the Odoo service if necessary

2. **Module Installation Issues**
   - If errors occur immediately after installing the module, try updating the module:
     ```
     ./odoo-bin -u ak_superset_analytics -d your_database
     ```
   - Check for any dependency issues in the logs

3. **PyJWT Installation**
   - Ensure the PyJWT package is properly installed:
     ```
     pip install PyJWT
     ```
   - If using a custom Python environment, make sure it's accessible to Odoo

4. **Run the Diagnostic Script**
   - We've included a diagnostic script that can help identify and fix common issues:
     ```
     # Start the Odoo shell
     python3 odoo-bin shell -d your_database_name -c your_config_file.conf
     
     # In the Odoo shell, run:
     exec(open('addons-custom/ak_superset_analytics/tools/diagnostic.py').read())
     ```
   - The script will check for common issues and attempt to fix them
   - After running the script, restart your Odoo server

## Superset Connection Issues

If the Odoo module is working but you can't connect to Superset:

1. **Check Superset Configuration**
   - Verify that the Superset configuration has been updated according to the [configuration guide](superset_configuration.md)
   - Ensure the JWT secret keys match between Odoo and Superset
   - Check that CORS is properly configured to allow requests from your Odoo domain

2. **Network Connectivity**
   - Ensure that the Odoo server can reach the Superset server
   - Check firewall settings that might block connections
   - Verify that the Superset URL in the dashboard configuration is correct and accessible

3. **JWT Token Issues**
   - Check Superset logs for any JWT-related errors
   - Ensure the token is being correctly generated (you can add temporary logging in the Odoo module)
   - Verify the token expiration settings

## Dashboard Display Issues

If dashboards don't display correctly:

1. **Iframe Issues**
   - Some browsers or security settings might block iframes
   - Check browser console for any iframe-related errors
   - Ensure the Superset server has the correct embedding settings enabled
   - If you're experiencing authentication issues within the iframe, check that the sandbox attribute is properly set to allow authentication:
     ```xml
     sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-top-navigation"
     ```
   - The module includes automatic token refresh functionality that will attempt to reload the iframe with a fresh token if authentication issues are detected

2. **Navigation Within Superset Iframe**
   - When viewing a Superset dashboard in an iframe, the JWT token is only valid for the specific dashboard URL
   - If you click on Superset navigation elements like "Back to home" or other menu items, you will be taken to the Superset login page
   - This is expected behavior because navigating away from the authenticated dashboard URL invalidates the JWT authentication
   - To return to Odoo, use the browser's back button or the Odoo navigation menu
   - If you need to view different Superset dashboards, return to the Odoo dashboard list and select another dashboard

2. **Dashboard ID**
   - Verify that the Dashboard ID in the configuration matches the actual ID in Superset
   - The Dashboard ID can be found in the URL when viewing the dashboard in Superset

3. **User Permissions**
   - Ensure the user has the correct permissions in both Odoo and Superset
   - Check that the allowed groups are properly configured

## Login Page Issues

If you see a Superset login page when viewing a dashboard:

1. **JWT Authentication Not Configured in Superset**
   - Make sure you've configured Superset with the JWT authentication settings as described in the [configuration guide](superset_configuration.md)
   - The most common cause is that Superset is not configured to use JWT authentication
   - Verify that the `CustomSSOSecurityManager` class is properly defined in your Superset config.py

2. **JWT Secret Key Mismatch**
   - Ensure the JWT secret key in Odoo matches the one in Superset
   - Check the `jwt_secret` field in the dashboard configuration and the `JWT_SECRET_KEY` in Superset's config.py
   - Try updating the secret key in both systems to ensure they match exactly

3. **CORS Configuration**
   - Make sure the CORS settings in Superset allow requests from your Odoo domain
   - Update the `origins` list in the CORS_OPTIONS in Superset's config.py
   - Ensure that `ENABLE_CORS = True` is set in Superset's config.py

4. **Superset Security Manager**
   - Verify that the CustomSSOSecurityManager is properly configured in Superset
   - Check Superset logs for any errors related to the security manager
   - Ensure that `CUSTOM_SECURITY_MANAGER = CustomSSOSecurityManager` is set in Superset's config.py

5. **Token Format**
   - Check the format of the JWT token being generated
   - You can see the token in the URL when testing the connection
   - Ensure it contains all the required fields (username, email, first_name, last_name, exp)

6. **Superset User Credentials**
   - Verify that the Superset user credentials configured in the dashboard are correct
   - Ensure the username and email match a valid user in Superset
   - Try using a different Superset user if the current one is not working
   - Check if the user has the necessary permissions in Superset to view the dashboard

6. **URL Format**
    - The URL format for accessing Superset dashboards with JWT authentication may vary depending on your Superset installation
    - The module currently uses:
      ```
      https://your-superset-domain.com/superset/dashboard/{dashboard_id}/?jwt=your_jwt_token
      ```
    - If this doesn't work, you may need to try other formats as described in the "URL Format Issues" section below

7. **Restart Superset and Odoo**
   - After making configuration changes, restart both Superset and Odoo
   - This ensures that all changes are properly applied

8. **Check Browser Console**
   - Open your browser's developer tools and check the console for any errors
   - Look for CORS errors or other issues that might prevent the JWT token from being processed

9. **Run the Diagnostic Script**
   - Use the diagnostic script included with this module to check for common issues:
     ```
     # In the Odoo shell
     exec(open('addons-custom/ak_superset_analytics/tools/diagnostic.py').read())
     ```

## URL Format Issues

If you encounter "Not Found" or 404 errors when trying to access dashboards:

1. **Check the URL Format**
   - Different Superset installations may use different URL formats
   - The module uses the same URL format for both viewing methods:
      - For both "New Window" view and iframe embedding: `/superset/dashboard/{dashboard_id}/?jwt={token}`
   - If this doesn't work, you may need to try other formats such as:
      - `/dashboard/{dashboard_id}/?jwt={token}`
      - `/login/?jwt={token}&dashboard_id={dashboard_id}`
   - You can modify the URL formats in the `get_embedded_url` and `get_embedded_url_for_iframe` methods in `superset_dashboard.py`

2. **Verify Dashboard ID**
   - Make sure the Dashboard ID in the configuration matches the actual ID in Superset
   - The Dashboard ID can be found in the URL when viewing the dashboard in Superset

3. **Check Superset Configuration**
   - Ensure that the Superset server is properly configured for JWT authentication
   - The CustomSSOSecurityManager should be set up to handle JWT tokens

## Viewing Method Issues

The module provides two different methods for viewing dashboards:

1. **Iframe View Issues**
   - Iframe view is the default method but may have issues due to browser security restrictions
   - Check that the sandbox attribute is properly set to allow authentication
   - Look for CORS errors in the browser console
   - Some Superset configurations may not work with iframe embedding at all
   - Be aware that navigating within Superset (clicking on Superset menus, "Back to home", etc.) will cause you to lose authentication and see the login page

2. **New Window View Issues**
   - If the new window view doesn't work, check that pop-ups are not being blocked by your browser
   - Ensure the JWT token is being generated correctly
   - Check that the Superset URL is correct and accessible

## Debugging Tips

1. **Try Different Viewing Methods**
   - If one viewing method doesn't work, try the other
   - The new window view is generally more reliable
   - The iframe view keeps you within Odoo but may have authentication issues

2. **Enable Developer Mode in Odoo**
   - This will provide more detailed error messages
   - Access it by adding ?debug=1 to the URL

3. **Check Browser Console**
   - Many JavaScript errors will appear in the browser console
   - Look for CORS errors, which are common in iframe integrations

4. **Temporary Logging**
   - Add temporary logging statements in the module's Python code to track the flow
   - Check the Odoo logs for these messages

5. **Test with a Simple Dashboard**
   - Create a simple test dashboard in Superset to isolate issues
   - Once that works, move on to more complex dashboards

## Server Errors After Module Installation

If you experience server errors immediately after installing this module:

1. **Check for Dependency Conflicts**
   - The module might conflict with other installed modules
   - Check the Odoo server logs for specific error messages

2. **Verify Database Integrity**
   - Database integrity issues can cause server errors
   - Run the following command to check for database issues:
     ```
     ./odoo-bin -d your_database --db_user your_db_user --db_password your_db_password -c your_config_file.conf --check
     ```

3. **Temporarily Disable the Module**
   - If the server won't start, you can temporarily disable the module by updating the ir_module_module table in the database:
     ```sql
     UPDATE ir_module_module SET state='uninstalled' WHERE name='ak_superset_analytics';
     ```

4. **Run the Diagnostic Script**
   - The diagnostic script can help identify and fix issues with the module
   - Follow the instructions in the "Run the Diagnostic Script" section above

## Getting Support

If you continue to experience issues after trying these troubleshooting steps, please contact kardan.digital with the following information:

1. Detailed description of the issue
2. Steps to reproduce the problem
3. Odoo server logs
4. Browser console logs
5. Screenshots of any error messages