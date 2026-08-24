/**
 * ROYAL ROSE MILK — Universal Centralized API Client (v2026.10)
 *
 * Frontend Host: https://royalrosmilk.netlify.app
 * Production Flask Backend: https://royal-rosegunicorn-app-ap.onrender.com
 */

(function () {
    "use strict";

    const PRODUCTION_API_URL = "https://royal-rosegunicorn-app-ap.onrender.com";

    const hostname = window.location.hostname || "";
    const port = window.location.port || "";
    const protocol = window.location.protocol || "";

    let resolvedBaseUrl = PRODUCTION_API_URL;

    // Only use local URL when explicitly running on localhost / private network
    if (
        hostname === "localhost" ||
        hostname === "127.0.0.1" ||
        hostname === "0.0.0.0" ||
        hostname.startsWith("192.168.") ||
        hostname.startsWith("10.")
    ) {
        if (protocol === "http:" && (port === "5000" || port === "")) {
            resolvedBaseUrl = ""; // Directly served by local Flask
        } else {
            resolvedBaseUrl = `http://${hostname}:5000`;
        }
    } else {
        // Netlify, Render, GitHub Pages, Custom Domains, file:// -> ALWAYS use live Render API
        resolvedBaseUrl = PRODUCTION_API_URL;
    }

    resolvedBaseUrl = resolvedBaseUrl.replace(/\/+$/, "");

    console.log("========================================");
    console.log("♛ ROYAL ROSE MILK API CLIENT (v2026.10)");
    console.log("Frontend Host :", window.location.origin || "file://");
    console.log("Backend Target:", resolvedBaseUrl);
    console.log("========================================");

    window.ROYAL_BACKEND_URL = resolvedBaseUrl;

    const royalApi = {
        baseUrl: resolvedBaseUrl,
        productionUrl: PRODUCTION_API_URL,

        getBaseUrl() {
            return this.baseUrl || PRODUCTION_API_URL;
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

        getFullUrl(endpoint) {
            if (endpoint.startsWith("http://") || endpoint.startsWith("https://")) {
                return endpoint;
            }
            const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
            const base = this.baseUrl || PRODUCTION_API_URL;
            return `${base}${cleanEndpoint}`;
        },

        async request(endpoint, options = {}) {
            const fullUrl = this.getFullUrl(endpoint);

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

            console.log(`[RoyalApi] ${fetchOptions.method || "GET"} -> ${fullUrl}`);

            try {
                const response = await fetch(fullUrl, fetchOptions);
                const contentType = response.headers.get("content-type") || "";

                let data = {};
                if (contentType.includes("application/json")) {
                    data = await response.json().catch(() => ({}));
                } else {
                    const text = await response.text().catch(() => "");
                    let cleanMsg = text;
                    if (text.includes("<!doctype html>") || text.includes("<html") || text.includes("<title>")) {
                        cleanMsg = response.status === 500 
                            ? "Internal server error. Please try again." 
                            : `Request failed with status ${response.status}.`;
                    }
                    data = {
                        success: response.ok,
                        message: cleanMsg
                    };
                }

                console.log(`[RoyalApi] Response ${response.status}:`, data);

                return {
                    ok: response.ok,
                    status: response.status,
                    data: data
                };
            } catch (err) {
                console.error(`[RoyalApi Error] ${fullUrl}:`, err);
                return {
                    ok: false,
                    status: 0,
                    data: {
                        success: false,
                        message: "Unable to connect to Royal Rose Milk backend. Please check network connection."
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