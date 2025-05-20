odoo.define('ak_crm.tree_widget', function (require) {
    "use strict";

    var core = require('web.core');
    var FieldOne2Many = require('web.relational_fields').FieldOne2Many;
    var registry = require('web.field_registry');

    var JsTreeWidget = FieldOne2Many.extend({
        template: 'JsTreeWidget',
//        events: _.extend({}, FieldOne2Many.prototype.events, {
//            'click .jstree-anchor': '_onTreeItemClick',
//        }),
        start: function () {
            this.$tree = this.$(".jstree");
            return this._super();
        },
        _render: function () {
            var self = this;
            // Retrieve records from the specified model
            this._rpc({
                model: this.attrs.options.model,
                method: 'search_read',
                fields: [this.attrs.options.parent_field, this.attrs.options.display_field],
            }).then(function (records) {
                // Convert records into a format suitable for jstree
                var data = _.map(records, function (record) {
                    return {
                        id: record.id,
                        parent: record[self.attrs.options.parent_field][0] || "#",
                        text: record[self.attrs.options.display_field],
                    };
                });
                // Render the tree
                self.$tree.jstree({
                    'core': {
                        'data': data
                    }
                });
            });
        },
        _onTreeItemClick: function (event) {
            // Handle click events on tree items here
        }
    });

    registry.add('tree_widget', JsTreeWidget);

    return JsTreeWidget;
});
