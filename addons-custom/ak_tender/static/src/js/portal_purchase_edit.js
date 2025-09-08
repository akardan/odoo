// Use vanilla JavaScript to avoid dependency issues

// Add global error handler
window.onerror = function(message, source, lineno, colno, error) {
    console.error('Global error caught:', message, 'at', source, lineno, colno);
    console.error('Error object:', error);
    return false;
};

// Global variables to track state
var portalPurchaseEditInitialized = false;
var saveInProgress = false;
var successMessageShown = false;

// Execute immediately and also on DOMContentLoaded to ensure it runs
function initializePortalPurchaseEdit() {
    // Skip if already initialized
    if (portalPurchaseEditInitialized) {
        return;
    }
    
    try {
        // Set the initialization flag
        portalPurchaseEditInitialized = true;
        
        // Function to handle save all button click
        function handleSaveAllButtonClick(event) {
            try {
                event.preventDefault();
                
                // Prevent duplicate processing
                if (saveInProgress) {
                    return;
                }
                
                // Reset success message flag
                successMessageShown = false;
                
                // Set save in progress flag
                saveInProgress = true;
                
                var button = event.currentTarget;
                
                // Get order ID and token from URL
                var urlParams = new URLSearchParams(window.location.search);
                var pathParts = window.location.pathname.split('/');
                var orderId = pathParts[pathParts.length - 1];
                var token = urlParams.get('access_token');
                
                if (!orderId) {
                    console.error('Could not determine order ID');
                    alert('Sipariş ID bulunamadı');
                    saveInProgress = false;
                    return;
                }
                
                // Show loading indicator
                button.disabled = true;
                button.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Kaydediliyor...';
                
                // Get all order lines
                var orderLines = [];
                var table = document.getElementById('purchase_order_table');
                var rows = table.querySelectorAll('tbody tr');
                
                // Clear validation classes
                var editableFields = document.querySelectorAll('.editable-field');
                editableFields.forEach(function(field) {
                    field.classList.remove('is-invalid');
                    field.classList.remove('is-valid');
                });
                
                // Process each row
                var hasErrors = false;
                rows.forEach(function(row) {
                    // Skip section and note rows
                    if (row.classList.contains('o_line_section') || row.classList.contains('fst-italic') || row.classList.contains('is-subtotal')) {
                        return;
                    }
                    
                    // Get the line ID from the inputs
                    var inputs = row.querySelectorAll('input, select, textarea');
                    if (inputs.length === 0) {
                        return;
                    }
                    
                    // Extract line ID from the first input's name (e.g., price_unit_line_123)
                    var firstInput = inputs[0];
                    var nameMatch = firstInput.name.match(/.*_line_(\d+)/);
                    if (!nameMatch) {
                        return;
                    }
                    
                    var lineId = nameMatch[1];
                    
                    // Get all editable fields for this line
                    var priceInput = row.querySelector('input[name="price_unit_line_' + lineId + '"]');
                    var dateInput = row.querySelector('input[name="delivery_date_line_' + lineId + '"]');
                    var warrantyInput = row.querySelector('select[name="warranty_period_line_' + lineId + '"]');
                    var supplierRefInput = row.querySelector('input[name="supplier_ref_line_' + lineId + '"]'); // Now hidden
                    var altMaterialsInput = row.querySelector('textarea[name="alt_materials_line_' + lineId + '"]');
                    var nameInput = row.querySelector('textarea[name="name_line_' + lineId + '"]');
                    var discountInput = row.querySelector('input[name="discount_line_' + lineId + '"]');
                    var taxesInput = row.querySelector('select[name="taxes_line_' + lineId + '"]');
                    
                    if (!priceInput) {
                        return;
                    }
                    
                    // Get values
                    var priceUnit = parseFloat(priceInput.value);
                    var deliveryDate = dateInput ? dateInput.value : null;
                    var warrantyPeriod = warrantyInput && warrantyInput.value ? parseInt(warrantyInput.value) : false;
                    var supplierRef = supplierRefInput ? supplierRefInput.value : '';
                    var altMaterials = altMaterialsInput ? altMaterialsInput.value : '';
                    var name = nameInput ? nameInput.value : '';
                    var discount = discountInput ? parseFloat(discountInput.value) : 0;
                    var taxesId = taxesInput && taxesInput.value ? parseInt(taxesInput.value) : false;
                    
                    // Validate price
                    if (isNaN(priceUnit) || priceUnit < 0) {
                        alert('Lütfen geçerli bir fiyat giriniz (Satır: ' + lineId + ')');
                        priceInput.classList.add('is-invalid');
                        hasErrors = true;
                        return;
                    }
                    
                    // Validate discount
                    if (isNaN(discount) || discount < 0 || discount > 100) {
                        alert('Lütfen geçerli bir indirim yüzdesi giriniz (0-100 arası) (Satır: ' + lineId + ')');
                        discountInput.classList.add('is-invalid');
                        hasErrors = true;
                        return;
                    }
                    
                    // Prepare line data
                    var lineData = {
                        line_id: parseInt(lineId),
                        price_unit: priceUnit,
                        discount: discount
                    };
                    
                    // Add optional fields if they have values
                    if (deliveryDate) {
                        lineData.date_planned = deliveryDate; // Already in YYYY-MM-DD format from the date input
                    }
                    
                    if (warrantyPeriod) {
                        lineData.warranty_period = warrantyPeriod;
                    }
                    
                    lineData.supplier_ref = supplierRef;
                    lineData.alt_materials = altMaterials;
                    lineData.name = name;
                    
                    if (taxesId) {
                        lineData.taxes_id = [[6, 0, [taxesId]]]; // Format for many2many field update
                    }
                    
                    // Add to order lines array
                    orderLines.push(lineData);
                });
                
                // If there are validation errors, stop
                if (hasErrors) {
                    button.disabled = false;
                    button.innerHTML = '<i class="fa fa-save"></i> Tüm Değişiklikleri Kaydet';
                    saveInProgress = false;
                    return;
                }
                
                // If no lines to update, show message
                if (orderLines.length === 0) {
                    alert('Güncellenecek satır bulunamadı');
                    button.disabled = false;
                    button.innerHTML = '<i class="fa fa-save"></i> Tüm Değişiklikleri Kaydet';
                    saveInProgress = false;
                    return;
                }
                
                // Get payment term value
                var paymentTermSelect = document.querySelector('select[name="payment_term_id"]');
                var paymentTermId = paymentTermSelect ? paymentTermSelect.value : false;
                console.log('Payment term selected:', paymentTermId);
                
                // Prepare params object for all lines
                var params = {
                    order_id: parseInt(orderId),
                    access_token: token,
                    lines: orderLines,
                    payment_term_id: paymentTermId
                };
                
                // Send the request using XMLHttpRequest
                var xhr = new XMLHttpRequest();
                xhr.open('POST', '/my/purchase/update_supplier_order', true);
                xhr.setRequestHeader('Content-Type', 'application/json');
                
                xhr.onload = function() {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        button.disabled = false;
                        button.innerHTML = '<i class="fa fa-save"></i> Tüm Değişiklikleri Kaydet';
                        
                        try {
                            var data = JSON.parse(xhr.responseText);
                            
                            if (data.result && data.result.error) {
                                // Show error
                                console.error('Error:', data.result.error);
                                alert('Hata: ' + data.result.error);
                                saveInProgress = false;
                                return;
                            } else if (data.error) {
                                // Show error
                                console.error('Error:', data.error);
                                alert('Hata: ' + data.error);
                                saveInProgress = false;
                                return;
                            }
                            
                            // Show success message only once
                            if (!successMessageShown) {
                                alert('Değişiklikler başarıyla kaydedildi!');
                                successMessageShown = true;
                            }
                            
                            // Add success class to all inputs
                            editableFields.forEach(function(field) {
                                field.classList.add('is-valid');
                            });
                            
                            // Update the total amount on the left side if it exists
                            if (data.result && data.result.amount_total) {
                                // Try to find the total amount element - it's the first h1 or h2 or h3 in the sidebar
                                var totalAmountElement = document.querySelector('h1, h2, h3');
                                if (totalAmountElement && totalAmountElement.textContent.includes('$')) {
                                    console.log('Found total amount element:', totalAmountElement);
                                    
                                    // Get the updated amount from the response
                                    var amountTotal = data.result.amount_total;
                                    
                                    // If the response contains HTML (like <span class="o_price_total">$ 44.000,00</span>)
                                    // Extract just the text
                                    if (amountTotal.includes('<')) {
                                        var tempDiv = document.createElement('div');
                                        tempDiv.innerHTML = amountTotal;
                                        amountTotal = tempDiv.textContent || tempDiv.innerText || '';
                                    }
                                    
                                    // Update the element
                                    totalAmountElement.textContent = amountTotal;
                                    console.log('Updated total amount to:', amountTotal);
                                } else {
                                    console.log('Total amount element not found');
                                }
                            }
                            
                            // Remove success class after a delay
                            setTimeout(function() {
                                editableFields.forEach(function(field) {
                                    field.classList.remove('is-valid');
                                });
                                saveInProgress = false;
                            }, 2000);
                            
                        } catch (e) {
                            console.error('Error parsing response:', e);
                            alert('Bir hata oluştu: ' + e.message);
                            saveInProgress = false;
                        }
                    } else {
                        console.error('AJAX error:', xhr.status, xhr.statusText);
                        console.error('Response:', xhr.responseText);
                        alert('Bir hata oluştu: ' + xhr.statusText);
                        button.disabled = false;
                        button.innerHTML = '<i class="fa fa-save"></i> Tüm Değişiklikleri Kaydet';
                        saveInProgress = false;
                    }
                };
                
                xhr.onerror = function() {
                    console.error('AJAX error: Network error');
                    alert('Bir ağ hatası oluştu. Lütfen tekrar deneyiniz.');
                    button.disabled = false;
                    button.innerHTML = '<i class="fa fa-save"></i> Tüm Değişiklikleri Kaydet';
                    saveInProgress = false;
                };
                
                // Log the request data for debugging
                console.log('Sending request with params:', params);
                
                xhr.send(JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: params,
                    id: Math.floor(Math.random() * 1000000000)
                }));
            } catch (e) {
                console.error('Error in handleSaveAllButtonClick:', e);
                alert('Error processing save: ' + e.message);
                saveInProgress = false;
            }
        }
    
        // Add event listener to the save all button
        var saveAllButton = document.getElementById('save-all-btn');
        if (saveAllButton) {
            // Remove any existing event listeners to avoid duplicates
            var newSaveAllButton = saveAllButton.cloneNode(true);
            saveAllButton.parentNode.replaceChild(newSaveAllButton, saveAllButton);
            saveAllButton = newSaveAllButton;
            
            // Add only one event listener
            saveAllButton.addEventListener('click', handleSaveAllButtonClick);
        } else {
            console.error('Save All button not found');
            // Try again after a short delay to ensure DOM is fully loaded
            setTimeout(function() {
                try {
                    if (portalPurchaseEditInitialized) {
                        return; // Skip if already initialized
                    }
                    
                    var saveAllButton = document.getElementById('save-all-btn');
                    if (saveAllButton) {
                        // Remove any existing event listeners to avoid duplicates
                        var newSaveAllButton = saveAllButton.cloneNode(true);
                        saveAllButton.parentNode.replaceChild(newSaveAllButton, saveAllButton);
                        saveAllButton = newSaveAllButton;
                        
                        // Add only one event listener
                        saveAllButton.addEventListener('click', handleSaveAllButtonClick);
                    } else {
                        console.error('Save All button still not found after delay');
                    }
                } catch (e) {
                    console.error('Error in delayed button search:', e);
                }
            }, 1000);
        }
    } catch (e) {
        console.error('Error in initializePortalPurchaseEdit:', e);
    }
}

// Run initialization only once
if (!portalPurchaseEditInitialized) {
    try {
        initializePortalPurchaseEdit();
        
        // Add event listeners for info icons
        var infoIcons = document.querySelectorAll('.info-toggle');
        infoIcons.forEach(function(icon) {
            icon.addEventListener('click', function(e) {
                e.preventDefault();
                var lineId = this.getAttribute('data-line-id');
                var descriptionField = document.getElementById('description_' + lineId);
                if (descriptionField) {
                    if (descriptionField.style.display === 'none') {
                        descriptionField.style.display = 'block';
                    } else {
                        descriptionField.style.display = 'none';
                    }
                }
            });
        });
    } catch (e) {
        console.error('Error running initialization:', e);
    }
}

// Also run on DOMContentLoaded if not already initialized
document.addEventListener('DOMContentLoaded', function() {
    if (!portalPurchaseEditInitialized) {
        try {
            initializePortalPurchaseEdit();
        } catch (e) {
            console.error('Error in DOMContentLoaded handler:', e);
        }
    }
});