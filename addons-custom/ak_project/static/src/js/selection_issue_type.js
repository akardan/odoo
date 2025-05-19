/** @odoo-module **/
// Buna gerek var mı ya da nerede kullanılır tam anlayamadım
import { qweb } from 'web.core';
import fieldRegistry from 'web.field_registry';    
import { FieldSelection } from 'web.relational_fields';
    

export const  SelectionIssueType = FieldSelection.extend({
    _template: 'ak_project.issueTypeWithImage',

    /**
     * @override
     */    
    init: function () {        
        this._super.apply(this, arguments);
    },

    /**
     * @override
     */    
    _renderReadonly() {
        this._super.apply(this, arguments);
        if (this.value) {
            // var imgSrc = this._getImageSource(this.value);
            // if (imgSrc) {
            //     this.$el.html('<img src="' + imgSrc + '" class="selection-issue-type"/> ' + this.$el.html());
            // }
            this.$el.prepend(qweb.render(this._template, {
                value: this.value,
            }));              
        }
    },  
    _getImageSource: function (value) {
        if (value) 
            return '/ak_project/static/src/img/'+value+'.png';
        else
            return null;
    },
});

fieldRegistry.add('selection_issue_type', SelectionIssueType);