// Runtime configuration for the demo monitor frontend.
//
// The frontend is normally served by the in-stack Nginx container, which
// proxies /api/v1 to the local inventory-service and analytics-service.
// In that case the default below is correct and no override is needed.
//
// When the static frontend is hosted somewhere without a backend (for
// example on Vercel as a portfolio preview), there is no /api/v1 proxy.
// You can either:
//   1. Override window.__APP_CONFIG__.API_BASE_URL to point at a publicly
//      reachable backend, or
//   2. Leave it pointing at /api/v1 and accept that calls will fail. The
//      page still renders, with each panel showing its loading/error state
//      so a viewer can see the structure of the dashboard.
window.__APP_CONFIG__ = window.__APP_CONFIG__ || {};
window.__APP_CONFIG__.API_BASE_URL = window.__APP_CONFIG__.API_BASE_URL || '/api/v1';
