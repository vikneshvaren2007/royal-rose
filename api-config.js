/**
 * ROYAL ROSE MILK — Centralized API Configuration & Client
 *
 * Frontend:
 *   https://royalrosmilk.netlify.app
 *
 * Production Flask Backend:
 *   https://royal-rosegunicorn-app-ap.onrender.com
 *
 * Supports:
 *   - Netlify production
 *   - Render production
 *   - Local Flask (port 5000)
 *   - VS Code Live Server (port 5500)
 *   - file:// fallback
 */

(function () {
    "use strict";

    const host = window.location.hostname || "127.0.0.1";
    const protocol = window.location.protocol;
    const port = window.location.port;

    // ============================================================
    // PRODUCTION FLASK BACKEND
    // ============================================================
    const PRODUCTION_API_URL =
        "https://royal-rosegunicorn-app-ap.onrender.com";

    let baseUrl = "";

    // ============================================================
    // NETLIFY FRONTEND
    // ============================================================
    if (host === "royalrosmilk.netlify.app") {
        baseUrl = PRODUCTION_API_URL;
    }

    // ============================================================
    // RENDER FRONTEND
    // ============================================================
    else if (
        protocol === "https:" &&
        host.endsWith(".onrender.com")
    ) {
        baseUrl = window.location.origin;
    }

    // ============================================================
    // LOCAL DEVELOPMENT
    // ============================================================
    else if (protocol === "http:") {

        // Flask serving the frontend
        if (port === "5000") {
            baseUrl = "";
        }

        // VS Code Live Server / another local frontend server
        else {
            baseUrl = `http://${host}:5000`;
        }
    }

    // ============================================================
    // FILE:// FALLBACK
    // ============================================================
    else {
        baseUrl = "http://127.0.0.1:5000";
    }

    // Remove trailing slash if accidentally present
    baseUrl = baseUrl.replace(/\/+$/, "");

    console.log("========================================");
    console.log("ROYAL ROSE MILK API CONFIGURATION");
    console.log("Frontend:", window.location.origin);
    console.log("API Backend:", baseUrl || window.location.origin);
    console.log("========================================");

    // ============================================================
    // CENTRAL API CLIENT
    // ============================================================

    const royalApi = {

        baseUrl: baseUrl,

        // --------------------------------------------------------
        // Get API Base URL
        // --------------------------------------------------------
        getBaseUrl() {
            return this.baseUrl;
        },

        // --------------------------------------------------------
        // Admin Token
        // --------------------------------------------------------
        getAdminToken() {
            return localStorage.getItem("royalAdminToken") || "";
        },

        setAdminToken(token) {
            if (token) {
                localStorage.setItem("royalAdminToken", token);
            }
        },

        clearAdminToken() {
            localStorage.removeItem("royalAdminToken");
        },

        // --------------------------------------------------------
        // Main Request Function
        // --------------------------------------------------------
        async request(endpoint, options = {}) {

            const url = endpoint.startsWith("http")
                ? endpoint
                : `${this.baseUrl}${endpoint}`;

            const headers = {
                "Content-Type": "application/json",
                ...(options.headers || {})
            };

            // Add admin authentication token when available
            const token = this.getAdminToken();

            if (
                token &&
                !headers["Authorization"] &&
                !headers["X-Admin-Token"]
            ) {
                headers["Authorization"] = `Bearer ${token}`;
            }

            const fetchOptions = {
                ...options,
                headers: headers
            };

            console.log(
                `[RoyalApi] ${fetchOptions.method || "GET"} ${url}`
            );

            try {

                const response = await fetch(url, fetchOptions);

                const contentType =
                    response.headers.get("content-type") || "";

                let data = {};

                if (contentType.includes("application/json")) {
                    data = await response.json().catch(() => ({}));
                } else {
                    const text = await response.text().catch(() => "");
                    data = {
                        success: response.ok,
                        message: text
                    };
                }

                console.log(
                    `[RoyalApi] Response ${response.status}:`,
                    data
                );

                return {
                    ok: response.ok,
                    status: response.status,
                    data: data
                };

            } catch (err) {

                console.error(
                    `[RoyalApi Error] ${endpoint}:`,
                    err
                );

                return {
                    ok: false,
                    status: 0,
                    data: {
                        success: false,
                        message:
                            "Unable to connect to the Royal Rose Milk backend. Please try again."
                    },
                    error: err
                };
            }
        },

        // --------------------------------------------------------
        // GET
        // --------------------------------------------------------
        async get(endpoint, options = {}) {

            return this.request(endpoint, {
                ...options,
                method: "GET"
            });
        },

        // --------------------------------------------------------
        // POST
        // --------------------------------------------------------
        async post(endpoint, body = {}, options = {}) {

            return this.request(endpoint, {
                ...options,
                method: "POST",
                body: JSON.stringify(body)
            });
        },

        // --------------------------------------------------------
        // PUT
        // --------------------------------------------------------
        async put(endpoint, body = {}, options = {}) {

            return this.request(endpoint, {
                ...options,
                method: "PUT",
                body: JSON.stringify(body)
            });
        },

        // --------------------------------------------------------
        // DELETE
        // --------------------------------------------------------
        async delete(endpoint, options = {}) {

            return this.request(endpoint, {
                ...options,
                method: "DELETE"
            });
        },

        // --------------------------------------------------------
        // Backend Health Check
        // --------------------------------------------------------
        async checkHealth() {

            const res = await this.get("/api/health");

            return (
                res.ok &&
                res.data &&
                res.data.status === "ok"
            );
        }
    };

    // ============================================================
    // MAKE API CLIENT AVAILABLE TO ALL FRONTEND FILES
    // ============================================================

    window.royalApi = royalApi;

})();