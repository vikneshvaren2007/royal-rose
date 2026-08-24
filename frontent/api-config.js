/**
 * ROYAL ROSE MILK — Centralized Universal API Configuration & Client
 *
 * Netlify Frontend:
 *   https://royalrosmilk.netlify.app
 *
 * Production Render Flask Backend:
 *   https://royal-rosegunicorn-app-ap.onrender.com
 *
 * Fully supports:
 *   - Netlify production hosting (royalrosmilk.netlify.app & preview URLs)
 *   - Direct Render production serving
 *   - Local development (Flask port 5000, Live Server port 5500)
 *   - file:// protocol fallback
 */

(function () {
    "use strict";

    const PRODUCTION_API_URL = "https://royal-rosegunicorn-app-ap.onrender.com";

    let baseUrl = "";

    const host = window.location.hostname || "";
    const protocol = window.location.protocol || "";
    const port = window.location.port || "";

    // 1. Direct Render Backend (same origin)
    if (protocol === "https:" && host.endsWith(".onrender.com")) {
        baseUrl = window.location.origin;
    }
    // 2. Local Development (localhost / 127.0.0.1 / local network IP)
    else if (
        host === "localhost" ||
        host === "127.0.0.1" ||
        host === "0.0.0.0" ||
        host.startsWith("192.168.") ||
        host.startsWith("10.")
    ) {
        if (protocol === "http:" && (port === "5000" || port === "")) {
            baseUrl = "";
        } else {
            baseUrl = `http://${host}:5000`;
        }
    }
    // 3. Production Frontend (Netlify, Custom Domain, or Remote Client)
    else {
        baseUrl = PRODUCTION_API_URL;
    }

    // Sanitize trailing slash
    baseUrl = baseUrl.replace(/\/+$/, "");

    console.log("========================================");
    console.log("♛ ROYAL ROSE MILK API CLIENT (v3.0)");
    console.log("Frontend Host :", window.location.origin || "file://");
    console.log("Backend Target:", baseUrl || window.location.origin);
    console.log("========================================");

    // ============================================================
    // CENTRAL API CLIENT
    // ============================================================
    const royalApi = {
        baseUrl: baseUrl,
        productionUrl: PRODUCTION_API_URL,

        getBaseUrl() {
            return this.baseUrl;
        },

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

        async request(endpoint, options = {}) {
            const url = endpoint.startsWith("http")
                ? endpoint
                : `${this.baseUrl}${endpoint}`;

            const headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                ...(options.headers || {})
            };

            const token = this.getAdminToken();
            if (token && !headers["Authorization"] && !headers["X-Admin-Token"]) {
                headers["Authorization"] = `Bearer ${token}`;
                headers["X-Admin-Token"] = token;
            }

            const fetchOptions = {
                ...options,
                headers: headers
            };

            try {
                const response = await fetch(url, fetchOptions);
                const contentType = response.headers.get("content-type") || "";

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

                return {
                    ok: response.ok,
                    status: response.status,
                    data: data
                };
            } catch (err) {
                console.error(`[RoyalApi Error] ${endpoint}:`, err);
                return {
                    ok: false,
                    status: 0,
                    data: {
                        success: false,
                        message: "Unable to connect to Royal Rose Milk backend. Please ensure service is online."
                    },
                    error: err
                };
            }
        },

        async get(endpoint, options = {}) {
            return this.request(endpoint, { ...options, method: "GET" });
        },

        async post(endpoint, body = {}, options = {}) {
            return this.request(endpoint, {
                ...options,
                method: "POST",
                body: JSON.stringify(body)
            });
        },

        async put(endpoint, body = {}, options = {}) {
            return this.request(endpoint, {
                ...options,
                method: "PUT",
                body: JSON.stringify(body)
            });
        },

        async delete(endpoint, options = {}) {
            return this.request(endpoint, { ...options, method: "DELETE" });
        },

        async checkHealth() {
            const res = await this.get("/api/health");
            return res.ok && res.data && res.data.status === "ok";
        }
    };

    window.royalApi = royalApi;
})();