/**
 * ROYAL ROSE MILK — Centralized API Configuration & Client
 * Connects frontend to the Flask backend on port 5000 automatically,
 * whether served via Flask, Live Server (5500), or file system.
 */

(function () {
    // Dynamic Base URL Resolution (supports localhost, 127.0.0.1, and local network Wi-Fi IP on mobile)
    const host = window.location.hostname || "127.0.0.1";
    let baseUrl = `http://${host}:5000`;

    if (window.location.protocol.startsWith("http")) {
        // If served directly from Flask server on port 5000
        if (window.location.port === "5000") {
            baseUrl = "";
        }
    }

    const royalApi = {
        baseUrl: baseUrl,

        getBaseUrl() {
            return this.baseUrl;
        },

        getAdminToken() {
            return localStorage.getItem("royalAdminToken") || "";
        },

        setAdminToken(token) {
            localStorage.setItem("royalAdminToken", token);
        },

        clearAdminToken() {
            localStorage.removeItem("royalAdminToken");
        },

        async request(endpoint, options = {}) {
            const url = endpoint.startsWith("http") ? endpoint : `${this.baseUrl}${endpoint}`;
            const headers = {
                "Content-Type": "application/json",
                ...(options.headers || {})
            };

            const token = this.getAdminToken();
            if (token && !headers["Authorization"] && !headers["X-Admin-Token"]) {
                headers["Authorization"] = `Bearer ${token}`;
            }

            const fetchOptions = {
                ...options,
                headers: headers
            };

            try {
                const response = await fetch(url, fetchOptions);
                const data = await response.json().catch(() => ({}));
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
                        message: "Backend is currently unreachable. Please ensure the Royal Rose Milk backend is running."
                    }
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
            return res.ok && res.data.status === "ok";
        }
    };

    window.royalApi = royalApi;
})();
