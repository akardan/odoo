// Frontend JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Analytics tracking
    function trackEvent(action, data = {}) {
        if (typeof odoo !== 'undefined' && odoo.jsonRpc) {
            odoo.jsonRpc('/ekt/analytics', 'call', {
                'unique_code': window.prospectusCode || '',
                'action': action,
                ...data
            }).catch(function(error) {
                console.log('Analytics tracking error:', error);
            });
        }
    }

    // Track page visibility changes
    document.addEventListener('visibilitychange', function() {
        if (document.visibilityState === 'visible') {
            trackEvent('page_focus');
        } else {
            trackEvent('page_blur');
        }
    });

    // Track time spent on page
    let startTime = Date.now();
    window.addEventListener('beforeunload', function() {
        let timeSpent = Math.floor((Date.now() - startTime) / 1000);
        trackEvent('time_spent', { seconds: timeSpent });
    });

    // Print functionality
    if (document.getElementById('printBtn')) {
        document.getElementById('printBtn').addEventListener('click', function() {
            window.print();
            trackEvent('print');
        });
    }
});