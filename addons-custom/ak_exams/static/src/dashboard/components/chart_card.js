/** @odoo-module **/

import { Component, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

/**
 * Component for displaying a chart
 * Uses Chart.js for rendering
 */
export class ChartCard extends Component {
    static template = "ak_exams.ChartCard";
    static props = {
        title: { type: String },
        data: { type: Object },
        type: { type: String, optional: true },
        options: { type: Object, optional: true },
        showValues: { type: Boolean, optional: true },
    };
    
    static defaultProps = {
        type: "bar",
        options: {},
        showValues: false,
    };
    
    setup() {
        this.chartRef = useRef("chart");
        this.chart = null;
        this.chartJsLoaded = false;
        
        onMounted(async () => {
            // Lazy load Chart.js
            if (!window.Chart) {
                await loadJS("/web/static/lib/Chart/Chart.js");
            }
            
            this.chartJsLoaded = true;
            this.renderChart();
        });
        
        onWillUnmount(() => {
            if (this.chart) {
                this.chart.destroy();
                this.chart = null;
            }
        });
    }
    
    /**
     * Render the chart using Chart.js
     */
    renderChart() {
        if (!this.chartJsLoaded || !this.chartRef.el) {
            return;
        }
        
        const ctx = this.chartRef.el.getContext("2d");
        
        // Default options for all charts
        const defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "top",
                },
                title: {
                    display: false,
                },
            },
            layout: {
                padding: {
                    top: 10,
                    right: 10,
                    bottom: 10,
                    left: 10
                }
            },
        };
        
        // Set the height of the chart container
        if (this.chartRef.el && (this.props.type === 'bar' || this.props.type === 'horizontalBar')) {
            this.chartRef.el.style.height = '500px';
            this.chartRef.el.parentElement.style.height = '500px';
            this.chartRef.el.parentElement.parentElement.style.height = '500px';
        }
        
        // Merge default options with provided options
        const options = { ...defaultOptions, ...this.props.options };
        
        // If showValues is true, add a plugin to display values on the bars
        if (this.props.showValues && (this.props.type === "bar" || this.props.type === "horizontalBar")) {
            // Create a custom plugin to display values on the bars
            const showValuesPlugin = {
                id: 'showValues',
                afterDraw: (chart) => {
                    const ctx = chart.ctx;
                    ctx.save();
                    ctx.font = 'bold 12px Arial';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'bottom';
                    ctx.fillStyle = '#000';
                    
                    chart.data.datasets.forEach((dataset, i) => {
                        const meta = chart.getDatasetMeta(i);
                        meta.data.forEach((bar, index) => {
                            const data = dataset.data[index].toFixed(2) + '%';
                            ctx.fillText(data, bar.x, bar.y - 5);
                        });
                    });
                    ctx.restore();
                }
            };
            
            // Register the plugin
            Chart.register(showValuesPlugin);
        }
        
        // Create the chart
        this.chart = new Chart(ctx, {
            type: this.props.type,
            data: this.props.data,
            options: options,
        });
    }
}