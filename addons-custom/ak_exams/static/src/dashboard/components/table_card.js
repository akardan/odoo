/** @odoo-module **/

import { Component, useState } from "@odoo/owl";

/**
 * Component for displaying tabular data
 * Used for displaying lists of data in the dashboard
 */
export class TableCard extends Component {
    static template = "ak_exams.TableCard";
    static props = {
        title: { type: String },
        columns: { type: Array },
        rows: { type: Array },
        sortable: { type: Boolean, optional: true },
        defaultSort: { type: Object, optional: true },
    };
    
    static defaultProps = {
        sortable: false,
        defaultSort: { column: 0, direction: "asc" },
    };
    
    setup() {
        this.state = useState({
            sortColumn: this.props.defaultSort.column,
            sortDirection: this.props.defaultSort.direction,
        });
    }
    
    /**
     * Get the sorted rows based on the current sort column and direction
     * @returns {Array} - Sorted rows
     */
    get sortedRows() {
        if (!this.props.sortable) {
            return this.props.rows;
        }
        
        const { sortColumn, sortDirection } = this.state;
        const column = this.props.columns[sortColumn];
        
        return [...this.props.rows].sort((a, b) => {
            const aValue = a[column.field];
            const bValue = b[column.field];
            
            if (typeof aValue === "number" && typeof bValue === "number") {
                return sortDirection === "asc" ? aValue - bValue : bValue - aValue;
            }
            
            const aString = String(aValue).toLowerCase();
            const bString = String(bValue).toLowerCase();
            
            if (sortDirection === "asc") {
                return aString.localeCompare(bString);
            } else {
                return bString.localeCompare(aString);
            }
        });
    }
    
    /**
     * Handle column header click for sorting
     * @param {Number} columnIndex - Index of the clicked column
     */
    onColumnHeaderClick(columnIndex) {
        if (!this.props.sortable) {
            return;
        }
        
        if (this.state.sortColumn === columnIndex) {
            // Toggle sort direction
            this.state.sortDirection = this.state.sortDirection === "asc" ? "desc" : "asc";
        } else {
            // Change sort column
            this.state.sortColumn = columnIndex;
            this.state.sortDirection = "asc";
        }
    }
    
    /**
     * Get the sort indicator for a column header
     * @param {Number} columnIndex - Index of the column
     * @returns {String} - Sort indicator (▲, ▼, or empty string)
     */
    getSortIndicator(columnIndex) {
        if (!this.props.sortable || this.state.sortColumn !== columnIndex) {
            return "";
        }
        
        return this.state.sortDirection === "asc" ? "▲" : "▼";
    }
}