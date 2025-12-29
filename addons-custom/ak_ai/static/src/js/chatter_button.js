/** @odoo-module */

import { Chatter } from "@mail/chatter/web_portal/chatter";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";

// Patch Chatter to add Ask KAI button
patch(Chatter.prototype, {
    setup() {
        super.setup();
        // Inject required services
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");
        
        // Add state for AI input
        this.state = useState({
            showAiInput: false,
            aiMessage: "",
        });
    },

    /**
     * Check if current model has AI mixin
     */
    get hasAiButton() {
        const allowedModels = ['ak.tender', 'sale.order', 'purchase.order', 'res.partner'];
        return this.props.threadModel && allowedModels.includes(this.props.threadModel);
    },

    /**
     * Toggle AI input area
     */
    toggleAiInput() {
        this.state.showAiInput = !this.state.showAiInput;
        if (!this.state.showAiInput) {
            this.state.aiMessage = "";
        }
    },

    /**
     * Close AI input area
     */
    closeAiInput() {
        this.state.showAiInput = false;
        this.state.aiMessage = "";
    },

    /**
     * Send message to AI
     */
    async sendAiMessage() {
        const threadId = this.props.threadId;
        const threadModel = this.props.threadModel;
        const message = this.state.aiMessage;

        console.log("Ask KAI - Sending message for model:", threadModel, "ID:", threadId);
        
        if (!threadId) {
            this.notification.add("No record selected", { type: "warning" });
            return;
        }

        if (!message || !message.trim()) {
            this.notification.add("Please enter a message", { type: "warning" });
            return;
        }

        try {
            console.log("Ask KAI - Calling ORM to send message...");
            
            // Send message directly
            const result = await this.orm.call(
                threadModel,
                "send_ai_message",
                [[threadId], message.trim()]
            );

            console.log("Ask KAI - Message sent, result:", result);

            // Clear input and close AI area
            this.state.aiMessage = "";
            this.state.showAiInput = false;

            // Show success notification
            this.notification.add(
                "✓ Message sent to KAI! Response posted to chatter.",
                { type: "success" }
            );

            // Reload messages in chatter (same way as onPostCallback)
            if (this.state && this.state.thread) {
                this.load(this.state.thread, ["messages"]);
            }

        } catch (error) {
            console.error("Ask KAI - Error sending message:", error);
            this.notification.add(
                "Error: " + (error.data?.message || error.message || "Failed to send message"),
                { type: "danger" }
            );
        }
    },
});
