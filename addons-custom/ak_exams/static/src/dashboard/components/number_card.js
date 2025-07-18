/** @odoo-module **/

import { Component } from "@odoo/owl";

/**
 * Component for displaying a number with a title
 * Used for displaying statistics in the dashboard
 */
export class NumberCard extends Component {
    static template = "ak_exams.NumberCard";
    static props = {
        title: { type: String },
        value: { type: [Number, String] },
        suffix: { type: String, optional: true },
        prefix: { type: String, optional: true },
        color: { type: String, optional: true },
    };
    
    static defaultProps = {
        suffix: "",
        prefix: "",
        color: "primary",
    };
    
    /**
     * Format the value for display
     * @returns {String} - Formatted value
     */
    get formattedValue() {
        const value = this.props.value;
        if (typeof value === "number") {
            // Format number with 2 decimal places if needed
            return value % 1 === 0 ? value.toString() : value.toFixed(2);
        }
        return value;
    }
    
    /**
     * Get the CSS class for the card based on the color
     * @returns {String} - CSS class
     */
    get cardClass() {
        return `text-bg-${this.props.color}`;
    }
}