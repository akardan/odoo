/** @odoo-module **/

import { Component, useState, useEffect, useRef, onWillStart } from "@odoo/owl";
import { Layout } from "@web/search/layout";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

import { DashboardItem } from "./components/dashboard_item";
import { NumberCard } from "./components/number_card";
import { ChartCard } from "./components/chart_card";
import { TableCard } from "./components/table_card";

/**
 * Main dashboard component
 * Uses the Layout component for the standard Odoo layout
 */
export class SurveyDashboard extends Component {
    static template = "ak_exams.SurveyDashboard";
    static components = { Layout, DashboardItem, NumberCard, ChartCard, TableCard };
    
    setup() {
        this.dashboardService = useService("survey_dashboard");
        this.actionService = useService("action");
        this.orm = useService("orm");
        
        this.state = useState({
            surveyId: null,
            teamId: null,
            surveys: [],
            teams: [],
            loading: true,
        });
        
        onWillStart(async () => {
            // Load surveys and teams
            const [surveys, teams] = await Promise.all([
                this.orm.searchRead("survey.survey", [["survey_type", "=", "assessment"]], ["id", "title"]),
                this.orm.searchRead("crm.team", [], ["id", "name"]),
            ]);
            
            this.state.surveys = surveys;
            this.state.teams = teams;
            
            // Load dashboard data
            await this.loadDashboardData();
            
            this.state.loading = false;
        });
    }
    
    /**
     * Load dashboard data using the dashboard service
     */
    async loadDashboardData() {
        this.dashboardData = await this.dashboardService.loadDashboardData(
            this.state.surveyId,
            this.state.teamId
        );
    }
    
    /**
     * Handle survey change
     * @param {Event} event - Change event
     */
    async onSurveyChange(event) {
        const surveyId = parseInt(event.target.value, 10) || null;
        this.state.surveyId = surveyId;
        this.state.loading = true;
        await this.loadDashboardData();
        this.state.loading = false;
    }
    
    /**
     * Handle team change
     * @param {Event} event - Change event
     */
    async onTeamChange(event) {
        const teamId = parseInt(event.target.value, 10) || null;
        this.state.teamId = teamId;
        this.state.loading = true;
        await this.loadDashboardData();
        this.state.loading = false;
    }
    
    /**
     * Get the control panel props for the Layout component
     * @returns {Object} - Control panel props
     */
    get controlPanelProps() {
        return {
            cp_content: {
                $buttons: this.renderButtons(),
                $searchview: this.renderSearchView(),
            },
        };
    }
    
    /**
     * Render the control panel buttons
     * @returns {Object} - Buttons element
     */
    renderButtons() {
        const buttonContainer = document.createElement("div");
        buttonContainer.className = "o_cp_buttons d-flex";
        
        const refreshButton = document.createElement("button");
        refreshButton.className = "btn btn-primary";
        refreshButton.textContent = _t("Refresh");
        refreshButton.addEventListener("click", () => this.onRefresh());
        
        buttonContainer.appendChild(refreshButton);
        
        return buttonContainer;
    }
    
    /**
     * Render the search view (filters)
     * @returns {Object} - Search view element
     */
    renderSearchView() {
        const searchContainer = document.createElement("div");
        searchContainer.className = "o_cp_searchview d-flex align-items-center";
        
        // Survey filter
        const surveyFilter = document.createElement("div");
        surveyFilter.className = "o_cp_searchview_filter me-3";
        
        const surveyLabel = document.createElement("label");
        surveyLabel.className = "me-2";
        surveyLabel.textContent = _t("Survey");
        
        const surveySelect = document.createElement("select");
        surveySelect.className = "form-select";
        surveySelect.addEventListener("change", (ev) => this.onSurveyChange(ev));
        
        // Add empty option
        const emptyOption = document.createElement("option");
        emptyOption.value = "";
        emptyOption.textContent = _t("All Surveys");
        surveySelect.appendChild(emptyOption);
        
        // Add survey options
        for (const survey of this.state.surveys) {
            const option = document.createElement("option");
            option.value = survey.id;
            option.textContent = survey.title;
            if (survey.id === this.state.surveyId) {
                option.selected = true;
            }
            surveySelect.appendChild(option);
        }
        
        surveyFilter.appendChild(surveyLabel);
        surveyFilter.appendChild(surveySelect);
        
        // Team filter
        const teamFilter = document.createElement("div");
        teamFilter.className = "o_cp_searchview_filter";
        
        const teamLabel = document.createElement("label");
        teamLabel.className = "me-2";
        teamLabel.textContent = _t("Team");
        
        const teamSelect = document.createElement("select");
        teamSelect.className = "form-select";
        teamSelect.addEventListener("change", (ev) => this.onTeamChange(ev));
        
        // Add empty option
        const emptyTeamOption = document.createElement("option");
        emptyTeamOption.value = "";
        emptyTeamOption.textContent = _t("All Teams");
        teamSelect.appendChild(emptyTeamOption);
        
        // Add team options
        for (const team of this.state.teams) {
            const option = document.createElement("option");
            option.value = team.id;
            option.textContent = team.name;
            if (team.id === this.state.teamId) {
                option.selected = true;
            }
            teamSelect.appendChild(option);
        }
        
        teamFilter.appendChild(teamLabel);
        teamFilter.appendChild(teamSelect);
        
        searchContainer.appendChild(surveyFilter);
        searchContainer.appendChild(teamFilter);
        
        return searchContainer;
    }
    
    /**
     * Handle refresh button click
     */
    async onRefresh() {
        this.state.loading = true;
        await this.loadDashboardData();
        this.state.loading = false;
    }
    
    /**
     * Get the pie chart data for the top performers
     * @returns {Object} - Chart.js data object
     */
    get topPerformersChartData() {
        // Limit to top 10 performers to prevent chart from becoming too large
        const performers = (this.dashboardData.topPerformers || []).slice(0, 10);
        const groupAverage = this.dashboardData.groupAverage || 0;
        
        return {
            labels: performers.map(p => p?.name || _t("Unknown")),
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                }
            },
            datasets: [
                {
                    label: _t("Score"),
                    data: performers.map(p => p?.score || 0),
                    backgroundColor: [
                        "#4CAF50", "#2196F3", "#FFC107", "#FF5722", "#9C27B0",
                        "#3F51B5", "#E91E63", "#009688", "#795548", "#607D8B"
                    ],
                    barThickness: 20,
                    maxBarThickness: 30,
                },
                {
                    label: _t("Overall Average"),
                    data: Array(performers.length).fill(groupAverage),
                    type: 'line',
                    borderColor: "#FF5722",
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: false,
                    tension: 0,
                }
            ],
            plugins: [{
                afterDraw: function(chart) {
                    var ctx = chart.ctx;
                    ctx.font = 'bold 12px Arial';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'bottom';
                    ctx.fillStyle = '#000';
                    
                    // Only show values for the bar dataset (index 0)
                    var meta = chart.getDatasetMeta(0);
                    meta.data.forEach(function(bar, index) {
                        var value = chart.data.datasets[0].data[index];
                        if (value !== undefined && value !== null) {
                            var data = value.toFixed(2);
                            ctx.fillText(data, bar.x, bar.y - 5);
                        }
                    });
                    
                    // No label for the baseline (group average)
                }
            }]
        };
    }
    
    /**
     * Get the bar chart data for the region averages
     * @returns {Object} - Chart.js data object
     */
    get regionAveragesChartData() {
        // Limit to top 10 regions to prevent chart from becoming too large
        const regions = (this.dashboardData.regionAverages || []).slice(0, 10);
        const groupAverage = this.dashboardData.groupAverage || 0;
        
        return {
            labels: regions.map(r => r?.name || _t("Unknown")),
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                }
            },
            datasets: [
                {
                    label: _t("Average Score"),
                    data: regions.map(r => r?.average || 0),
                    backgroundColor: "#2196F3",
                    barThickness: 20,
                    maxBarThickness: 30,
                },
                {
                    label: _t("Overall Average"),
                    data: Array(regions.length).fill(groupAverage),
                    type: 'line',
                    borderColor: "#FF5722",
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: false,
                    tension: 0,
                }
            ],
            plugins: [{
                afterDraw: function(chart) {
                    var ctx = chart.ctx;
                    ctx.font = 'bold 12px Arial';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'bottom';
                    ctx.fillStyle = '#000';
                    
                    // Only show values for the bar dataset (index 0)
                    var meta = chart.getDatasetMeta(0);
                    meta.data.forEach(function(bar, index) {
                        var value = chart.data.datasets[0].data[index];
                        if (value !== undefined && value !== null) {
                            var data = value.toFixed(2);
                            ctx.fillText(data, bar.x, bar.y - 5);
                        }
                    });
                    
                    // No label for the baseline (group average)
                }
            }]
        };
    }
    
    /**
     * Get the table data for the region rankings
     * @returns {Object} - Table data object
     */
    get regionRankingsTableData() {
        return {
            columns: [
                { name: _t("Rank"), field: "rank" },
                { name: _t("Region"), field: "name" },
                { name: _t("Average Score"), field: "average" },
            ],
            rows: (this.dashboardData.regionRankings || []).map(r => ({
                rank: r?.rank || 0,
                name: r?.name || _t("Unknown"),
                average: r?.average !== undefined && r?.average !== null ?
                    r.average.toFixed(2) : 'N/A',
            })),
        };
    }
    
    /**
     * Get the doughnut chart data for the Turkey average
     * @returns {Object} - Chart.js data object
     */
    get turkeyAverageChartData() {
        const average = this.dashboardData.groupAverage || 0;
        return {
            labels: [_t("Average Score"), _t("Remaining")],
            datasets: [{
                data: [average, 100 - average],
                backgroundColor: ["#FF9800", "#EEEEEE"],
            }],
        };
    }
}

// Register the dashboard component as a client action
registry.category("actions").add("ak_exams.survey_dashboard", SurveyDashboard);