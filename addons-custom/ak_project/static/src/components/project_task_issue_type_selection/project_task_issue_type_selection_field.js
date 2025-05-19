/** @odoo-module */

import { SelectionField } from '@web/views/fields/selection/selection_field';
import { registry } from '@web/core/registry';

export class ProjectTaskIssueTypeSelectionField extends SelectionField {
    setup() {
        super.setup();
    }

    get currentValue() {
        return this.props.value; // || this.options[0][0];
    }

}
ProjectTaskIssueTypeSelectionField.template = 'ak_project.ProjectTaskIssueTypeSelectionField';

registry.category('fields').add('selection_issue_type', ProjectTaskIssueTypeSelectionField);
