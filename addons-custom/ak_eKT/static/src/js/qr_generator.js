odoo.define('ak_eKT.qr_generator', function (require) {
"use strict";

var AbstractField = require('web.AbstractField');
var core = require('web.core');
var field_registry = require('web.field_registry');

var QrCodeField = AbstractField.extend({
    className: 'o_field_qr_code',
    supportedFieldTypes: ['char'],

    _render: function () {
        var self = this;
        var $qr = $('<div>').addClass('qr-code-display');
        
        if (this.value) {
            // QR kod oluştur
            $qr.qrcode({
                text: this.value,
                width: 200,
                height: 200,
                colorDark: "#000000",
                colorLight: "#ffffff"
            });
        } else {
            $qr.html('<p>QR kod oluşturulmadı</p>');
        }
        
        this.$el.html($qr);
    }
});

field_registry.add('qr_code', QrCodeField);

return QrCodeField;
});