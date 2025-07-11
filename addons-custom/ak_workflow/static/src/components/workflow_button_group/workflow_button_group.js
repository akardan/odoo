/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class WorkflowButtonGroup extends Component {
    static template = "ak_workflow.WorkflowButtonGroup";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            transitions: [],
        });

        onWillStart(async () => {
            await this.fetchTransitions();
        });
    }

    get record() {
        return this.props.record;
    }

    async fetchTransitions() {
        const transitionsData = await this.orm.call(
            this.record.resModel,
            "get_available_transitions",
            [this.record.resId]
        );
        this.state.transitions = transitionsData;
    }

    onButtonClick(transitionId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "ak.workflow.transition.wizard",
            name: "Execute Transition",
            views: [[false, "form"]],
            target: "new",
            context: {
                default_active_model: this.record.resModel,
                default_active_id: this.record.resId,
                default_transition_id: transitionId,
            },
        }, {
            onClose: () => {
                this.action.doAction({ type: 'ir.actions.client', tag: 'reload' });
            },
        });
    }
}

registry.category("view_widgets").add("workflow_button_group", {
    component: WorkflowButtonGroup,
});