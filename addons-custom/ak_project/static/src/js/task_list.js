/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { useService } from "@web/core/utils/hooks";

function setupProjectButton(controller) {
    const orm = useService('orm');
    const actionService = useService('action');
    const user = useService('user');        
    // contexte burada controller.props.context ile ulaşmam gerektiğini çok zorluklarla öğrendim!!!
    const isDisplay = controller.model.rootParams.resModel === "project.task" && !!controller.props.context.active_id;

    async function onViewProjectClick() {     
        const active_id = controller.model.rootParams.context.active_id;         
        if (active_id) {
            const action = await orm.call('project.project', 'get_project', [active_id]);
            actionService.doAction(action);
        } else {
            console.error('Active ID is not available.');
        }
    }


    return { isDisplay, onViewProjectClick };
}

patch(ListController.prototype, {
    async start() {
        await super.start();
        const { isDisplay, onViewProjectClick } = setupProjectButton(this);
        this.isDisplay = isDisplay;
        this.onViewProjectClick = onViewProjectClick;
    },
});

patch(KanbanController.prototype, {
    async start() {
        await super.start();
        const { isDisplay, onViewProjectClick } = setupProjectButton(this);
        this.isDisplay = isDisplay;
        this.onViewProjectClick = onViewProjectClick;
    },
});
