/** @odoo-module **/

import { Component, useState, useRef, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class AkAiChatWidget extends Component {
    static template = "ak_ai.ChatWidget";
    
    setup() {
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        
        this.state = useState({
            messages: [],
            isTyping: false,
            inputValue: "",
        });
        
        this.inputRef = useRef("input");
        
        onMounted(() => {
            this.loadConversation();
        });
    }
    
    async loadConversation() {
        if (!this.props.conversationId) return;
        
        try {
            const conversation = await this.rpc("/web/dataset/call_kw", {
                model: "ak_ai.conversation",
                method: "read",
                args: [[this.props.conversationId], ["message_ids"]],
                kwargs: {},
            });
            
            if (conversation.length > 0) {
                const messageIds = conversation[0].message_ids;
                const messages = await this.rpc("/web/dataset/call_kw", {
                    model: "ak_ai.message",
                    method: "read",
                    args: [messageIds, ["content", "message_type", "create_date", "rating"]],
                    kwargs: { order: "create_date asc" },
                });
                
                this.state.messages = messages;
            }
        } catch (error) {
            console.error("Error loading conversation:", error);
        }
    }
    
    async sendMessage() {
        const message = this.state.inputValue.trim();
        if (!message) return;
        
        // Add user message to UI
        this.state.messages.push({
            content: message,
            message_type: "user",
            create_date: new Date().toISOString(),
        });
        
        this.state.inputValue = "";
        this.state.isTyping = true;
        
        try {
            // Send message to backend
            const response = await this.rpc("/web/dataset/call_kw", {
                model: "ak_ai.conversation",
                method: "send_message",
                args: [this.props.conversationId, message, "user"],
                kwargs: {},
            });
            
            // Reload messages to get AI response
            await this.loadConversation();
            
        } catch (error) {
            console.error("Error sending message:", error);
            this.notification.add(_t("Error sending message"), { type: "danger" });
        } finally {
            this.state.isTyping = false;
        }
    }
    
    onKeyPress(event) {
        if (event.key === "Enter") {
            this.sendMessage();
        }
    }
    
    async rateMessage(messageId, rating) {
        try {
            await this.rpc("/web/dataset/call_kw", {
                model: "ak_ai.message",
                method: "rate_message",
                args: [messageId, rating],
                kwargs: {},
            });
            
            this.notification.add(_t("Thank you for your feedback!"), { type: "success" });
            await this.loadConversation();
            
        } catch (error) {
            console.error("Error rating message:", error);
            this.notification.add(_t("Error submitting rating"), { type: "danger" });
        }
    }
}