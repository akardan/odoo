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

// Global function for attachment preview
window.previewAttachment = function(model, id, field, filename) {
    try {
        // Determine file type based on extension
        var isImage = /\.(jpg|jpeg|png|gif|bmp)$/i.test(filename);
        var isPdf = /\.pdf$/i.test(filename);
        
        // Get the content URL - check if access_token exists in URL
        var urlParams = new URLSearchParams(window.location.search);
        var accessToken = urlParams.get('access_token');
        var contentUrl;
        
        if (accessToken) {
            // For portal users with access token, use our custom route
            contentUrl = '/tender/attachment/' + id + '/' + field + '?access_token=' + accessToken;
        } else {
            // For logged in users without access token, use standard web/content route
            contentUrl = '/web/content?model=' + model + '&id=' + id + '&field=' + field + '&filename=' + filename;
        }
        
        // Create modal for preview
        var modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'attachmentPreviewModal';
        modal.setAttribute('tabindex', '-1');
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-hidden', 'true');
        
        var modalDialog = document.createElement('div');
        modalDialog.className = 'modal-dialog modal-lg';
        modalDialog.setAttribute('role', 'document');
        
        var modalContent = document.createElement('div');
        modalContent.className = 'modal-content';
        
        var modalHeader = document.createElement('div');
        modalHeader.className = 'modal-header';
        
        var modalTitle = document.createElement('h5');
        modalTitle.className = 'modal-title';
        modalTitle.textContent = filename;
        
        var closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'btn-close';
        closeButton.setAttribute('data-dismiss', 'modal');
        closeButton.setAttribute('data-bs-dismiss', 'modal');
        closeButton.setAttribute('aria-label', 'Close');
        
        // Add click handler for manual close
        closeButton.onclick = function() {
            if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                var bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            } else if (typeof $ !== 'undefined') {
                $(modal).modal('hide');
            } else {
                modal.style.display = 'none';
                document.body.removeChild(modal);
            }
        };
        
        modalHeader.appendChild(modalTitle);
        modalHeader.appendChild(closeButton);
        
        var modalBody = document.createElement('div');
        modalBody.className = 'modal-body text-center';
        
        // Add content based on file type
        if (isImage) {
            var img = document.createElement('img');
            img.src = contentUrl;
            img.className = 'img-fluid';
            img.style.maxHeight = '70vh';
            modalBody.appendChild(img);
        } else if (isPdf) {
            var iframe = document.createElement('iframe');
            iframe.src = contentUrl;
            iframe.width = '100%';
            iframe.height = '85vh';
            iframe.style.minHeight = '600px';
            modalBody.appendChild(iframe);
        } else {
            // For other file types, show download link
            var downloadLink = document.createElement('a');
            downloadLink.href = contentUrl;
            downloadLink.className = 'btn btn-primary';
            downloadLink.target = '_blank';
            downloadLink.innerHTML = '<i class="fa fa-download"></i> İndir';
            modalBody.appendChild(downloadLink);
        }
        
        modalContent.appendChild(modalHeader);
        modalContent.appendChild(modalBody);
        modalDialog.appendChild(modalContent);
        modal.appendChild(modalDialog);
        
        // Add modal to body
        document.body.appendChild(modal);
        
        // Show modal using Bootstrap's modal method if available, otherwise use jQuery
        if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            var bsModal = new bootstrap.Modal(modal);
            bsModal.show();
            
            // Remove modal from DOM when hidden
            modal.addEventListener('hidden.bs.modal', function () {
                document.body.removeChild(modal);
            });
        } else if (typeof $ !== 'undefined') {
            $(modal).modal('show');
            
            // Remove modal from DOM when hidden
            $(modal).on('hidden.bs.modal', function () {
                document.body.removeChild(modal);
            });
        } else {
            // Fallback: just show the modal
            modal.style.display = 'block';
            modal.classList.add('show');
            
            // Add close functionality
            closeButton.onclick = function() {
                modal.style.display = 'none';
                document.body.removeChild(modal);
            };
        }
        
    } catch (e) {
        console.error('Error in previewAttachment:', e);
        alert('Dosya önizlemesi açılırken bir hata oluştu.');
    }
};

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
                    var currencyInput = row.querySelector('select[name="currency_line_' + lineId + '"]');
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
                    var currency = currencyInput && currencyInput.value ? parseInt(currencyInput.value) : false;
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
                        line_price_unit: priceUnit,
                        discount: discount
                    };
                    
                    // Add currency if selected
                    if (currency) {
                        lineData.line_currency_id = currency;
                    }
                    
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
                                
                                // Handle object errors properly
                                let errorMessage = '';
                                if (typeof data.result.error === 'object') {
                                    // Try to extract meaningful information from the error object
                                    if (data.result.error.message) {
                                        errorMessage = data.result.error.message;
                                    } else if (data.result.error.data && data.result.error.data.message) {
                                        errorMessage = data.result.error.data.message;
                                    } else {
                                        // If no specific message, stringify the object
                                        try {
                                            errorMessage = JSON.stringify(data.result.error);
                                        } catch (e) {
                                            errorMessage = 'Bilinmeyen hata';
                                        }
                                    }
                                } else {
                                    // If it's already a string, use it directly
                                    errorMessage = data.result.error;
                                }
                                
                                alert('Hata: ' + errorMessage);
                                saveInProgress = false;
                                return;
                            } else if (data.error) {
                                // Show error
                                console.error('Error:', data.error);
                                
                                // Handle object errors properly
                                let errorMessage = '';
                                if (typeof data.error === 'object') {
                                    // Try to extract meaningful information from the error object
                                    if (data.error.message) {
                                        errorMessage = data.error.message;
                                    } else if (data.error.data && data.error.data.message) {
                                        errorMessage = data.error.data.message;
                                    } else {
                                        // If no specific message, stringify the object
                                        try {
                                            errorMessage = JSON.stringify(data.error);
                                        } catch (e) {
                                            errorMessage = 'Bilinmeyen hata';
                                        }
                                    }
                                } else {
                                    // If it's already a string, use it directly
                                    errorMessage = data.error;
                                }
                                
                                alert('Hata: ' + errorMessage);
                                saveInProgress = false;
                                return;
                            }
                            
                            // Show success message only once
                            if (!successMessageShown) {
                                alert('Değişiklikler başarıyla kaydedildi!');
                                successMessageShown = true;
                            }
                            
                            // Reload the page to show updated values
                            setTimeout(function() {
                                window.location.reload();
                            }, 500);
                            
                        } catch (e) {
                            console.error('Error parsing response:', e);
                            alert('Bir hata oluştu: ' + e.message);
                            saveInProgress = false;
                        }
                    } else {
                        console.error('AJAX error:', xhr.status, xhr.statusText);
                        console.error('Response:', xhr.responseText);
                        
                        // Try to get more detailed error information
                        let errorMessage = 'Bir hata oluştu.';
                        
                        if (xhr.status) {
                            errorMessage += ' HTTP Kodu: ' + xhr.status;
                        }
                        
                        if (xhr.statusText) {
                            errorMessage += ' (' + xhr.statusText + ')';
                        }
                        
                        if (xhr.responseText) {
                            try {
                                // Try to parse the response as JSON
                                const errorData = JSON.parse(xhr.responseText);
                                if (errorData.error) {
                                    if (typeof errorData.error === 'object') {
                                        if (errorData.error.message) {
                                            errorMessage += ' Hata: ' + errorData.error.message;
                                        } else if (errorData.error.data && errorData.error.data.message) {
                                            errorMessage += ' Hata: ' + errorData.error.data.message;
                                        }
                                    } else {
                                        errorMessage += ' Hata: ' + errorData.error;
                                    }
                                }
                            } catch (parseError) {
                                // If not JSON, just log it
                                console.error('Could not parse error response:', parseError);
                            }
                        }
                        
                        alert(errorMessage);
                        button.disabled = false;
                        button.innerHTML = '<i class="fa fa-save"></i> Tüm Değişiklikleri Kaydet';
                        saveInProgress = false;
                    }
                };
                
                xhr.onerror = function(e) {
                    console.error('AJAX error: Network error', e);
                    
                    // Try to get more detailed error information
                    let errorMessage = 'Bir ağ hatası oluştu.';
                    
                    if (xhr.status) {
                        errorMessage += ' HTTP Kodu: ' + xhr.status;
                    }
                    
                    if (xhr.statusText) {
                        errorMessage += ' (' + xhr.statusText + ')';
                    }
                    
                    if (xhr.responseText) {
                        console.error('Response text:', xhr.responseText);
                        try {
                            // Try to parse the response as JSON
                            const errorData = JSON.parse(xhr.responseText);
                            if (errorData.error) {
                                if (typeof errorData.error === 'object') {
                                    if (errorData.error.message) {
                                        errorMessage += ' Hata: ' + errorData.error.message;
                                    } else if (errorData.error.data && errorData.error.data.message) {
                                        errorMessage += ' Hata: ' + errorData.error.data.message;
                                    }
                                } else {
                                    errorMessage += ' Hata: ' + errorData.error;
                                }
                            }
                        } catch (parseError) {
                            // If not JSON, just log it
                            console.error('Could not parse error response:', parseError);
                        }
                    }
                    
                    alert(errorMessage + ' Lütfen tekrar deneyiniz.');
                    button.disabled = false;
                    button.innerHTML = '<i class="fa fa-save"></i> Tüm Değişiklikleri Kaydet';
                    saveInProgress = false;
                };
                
                // Send the request
                
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