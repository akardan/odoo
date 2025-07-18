/** @odoo-module **/

import { registry } from "@web/core/registry";
import { memoize } from "@web/core/utils/functions";
import { reactive } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";

/**
 * Service to load and cache survey dashboard data
 */
export const surveyDashboardService = {
    dependencies: ["notification"],
    
    start(env, { notification }) {
        // Create a reactive object to store the dashboard data
        const dashboardData = reactive({
            topPerformers: [],
            regionAverages: [],
            regionRankings: [],
            groupAverage: 0,
            surveyId: null,
            teamId: null,
        });
        
        // Memoized function to load dashboard data
        const loadDashboardData = memoize(async (surveyId, teamId) => {
            try {
                const data = await rpc("/survey/dashboard/data", {
                    survey_id: surveyId || false,
                    team_id: teamId || false,
                });
                
                // Update the reactive object with the new data
                dashboardData.topPerformers = data.top_performers || [];
                dashboardData.regionAverages = data.region_averages || [];
                dashboardData.regionRankings = data.region_rankings || [];
                dashboardData.groupAverage = data.group_average || 0;
                dashboardData.surveyId = surveyId;
                dashboardData.teamId = teamId;
                
                return dashboardData;
            } catch (error) {
                notification.add(
                    _t("Failed to load dashboard data"),
                    { type: "danger" }
                );
                throw error;
            }
        });
        
        // Set up periodic refresh (every 10 minutes)
        setInterval(async () => {
            if (dashboardData.surveyId !== null || dashboardData.teamId !== null) {
                await loadDashboardData(dashboardData.surveyId, dashboardData.teamId);
            }
        }, 10 * 60 * 1000);
        
        return {
            /**
             * Load dashboard data for the given survey and team
             * @param {Number} surveyId - ID of the survey
             * @param {Number} teamId - ID of the team
             * @returns {Object} - Reactive dashboard data object
             */
            loadDashboardData,
            
            /**
             * Get the reactive dashboard data object
             * @returns {Object} - Reactive dashboard data object
             */
            getDashboardData() {
                return dashboardData;
            },
        };
    },
};

registry.category("services").add("survey_dashboard", surveyDashboardService);