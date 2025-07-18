/** @odoo-module **/

import { Component } from "@odoo/owl";

/**
 * Generic dashboard item component
 * Displays a card with a title and content
 */
export class DashboardItem extends Component {
    static template = "ak_exams.DashboardItem";
    static props = {
        size: { type: Number, optional: true },
        title: { type: String, optional: true },
        className: { type: String, optional: true },
        slots: { type: Object, optional: true },
    };
    
    static defaultProps = {
        size: 1,
        className: "",
    };
    
    /**
     * Compute the width of the dashboard item based on the size
     * @returns {String} - CSS width value
     */
    get itemStyle() {
        return `width: ${18 * this.props.size}rem;`;
    }
}