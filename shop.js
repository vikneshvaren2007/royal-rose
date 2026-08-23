/**
 * ROYAL ROSE MILK — LUXURY SHOP & COLLECTION CONTROLLER
 * Features:
 * 1. Categorized Catalogues: CLASSIC COLLECTION & SPECIALITY BLENDS
 * 2. 100% Unique High-Resolution Product Imagery
 * 3. Dynamic Filtering (All, Classic, Speciality) & Live Search
 * 4. Resilient Backend Sync with /api/products
 * 5. Cart Management & Direct Booking Redirection
 */

document.addEventListener("DOMContentLoaded", () => {

    /* ==========================================================================
       STATE & DOM ELEMENTS
       ========================================================================== */
    let cart = JSON.parse(localStorage.getItem("royalCart")) || [];
    let allProducts = [];
    let activeFilter = "all";
    let searchQuery = "";

    const classicGroup = document.getElementById("classicGroup");
    const specialityGroup = document.getElementById("specialityGroup");
    const classicGrid = document.getElementById("classicGrid");
    const specialityGrid = document.getElementById("specialityGrid");
    const noResultsMsg = document.getElementById("noResultsMsg");

    const cartCountBadge = document.getElementById("cartCount");
    const cartToast = document.getElementById("cartToast");
    const toastProductName = document.getElementById("toastProductName");
    const searchInput = document.getElementById("shopSearchInput");
    const filterButtons = document.querySelectorAll(".filter-btn");

    // Comprehensive Fallback Products with 100% Unique Imagery
    const fallbackProducts = [
        // CLASSIC COLLECTION
        {
            id: 1,
            name: "Royal Rose Classic",
            price: 149,
            description: "Smooth, chilled velvet whole milk infused with authentic Kannauj Damask rose extract.",
            image: "images/Classic Rose Milk.jpg",
            category: "Classic Collection",
            badge: "BESTSELLER",
            rating: 5,
            reviews_count: 154,
            available: 1,
            sold_out: 0
        },
        {
            id: 2,
            name: "Royal Rose Signature",
            price: 199,
            description: "Our flagship magnum opus. Concentrated damask rose absolute folded into rich whole cream with green cardamom.",
            image: "images/Royal Rose Milk.jpg",
            category: "Classic Collection",
            badge: "ROYAL FLAGSHIP",
            rating: 5,
            reviews_count: 230,
            available: 1,
            sold_out: 0
        },
        {
            id: 3,
            name: "Strawberry Rose Bliss",
            price: 169,
            description: "Sun-ripened hill strawberries pureed into fragrant rose milk for a vibrant sweet-tart balance.",
            image: "images/strawberry-rose.jpg",
            category: "Classic Collection",
            badge: "POPULAR CHOICE",
            rating: 5,
            reviews_count: 118,
            available: 1,
            sold_out: 0
        },
        {
            id: 4,
            name: "Rose Cardamom Royale",
            price: 179,
            description: "Fragrant green cardamom crushed with sun-dried damask rose petals in pure whole milk.",
            image: "images/cardamom-rose-milk.jpg",
            category: "Classic Collection",
            badge: "TRADITIONAL SPECIAL",
            rating: 5,
            reviews_count: 142,
            available: 1,
            sold_out: 0
        },

        // SPECIALITY BLENDS
        {
            id: 5,
            name: "Royal Kashmiri Saffron Elixir",
            price: 249,
            description: "Pure Grade-A Kashmiri saffron threads gently steeped in aromatic chilled Damask rose cream.",
            image: "images/saffron-rose-milk.jpg",
            category: "Speciality Blends",
            badge: "GOLD EDITION",
            rating: 5,
            reviews_count: 310,
            available: 1,
            sold_out: 0
        },
        {
            id: 6,
            name: "Royal Pistachio Velvet",
            price: 219,
            description: "Crushed roasted Iranian pistachios swirled with saffron-infused royal rose milk.",
            image: "images/pistachio-rose-milk.jpg",
            category: "Speciality Blends",
            badge: "ARTISANAL RESERVE",
            rating: 5,
            reviews_count: 186,
            available: 1,
            sold_out: 0
        },
        {
            id: 7,
            name: "Rose Badam Almond Cream",
            price: 209,
            description: "Finely slivered Mamra badam almonds steeped in slow-chilled floral velvet milk with silver leaf.",
            image: "images/almond-rose-milk.jpg",
            category: "Speciality Blends",
            badge: "CHEF'S RESERVE",
            rating: 5,
            reviews_count: 164,
            available: 1,
            sold_out: 0
        },
        {
            id: 8,
            name: "Tender Coconut Rose",
            price: 179,
            description: "Tender coastal coconut cream paired with aromatic rose floral absolute for tropical luxury.",
            image: "images/Rose Coconut Milk.jpg",
            category: "Speciality Blends",
            badge: "EXOTIC BLEND",
            rating: 5,
            reviews_count: 98,
            available: 1,
            sold_out: 0
        },
        {
            id: 9,
            name: "Dark Cocoa Rose Noir",
            price: 189,
            description: "Rich Dutch dark cocoa balanced with the delicate floral finish of fresh damask roses.",
            image: "images/Rose Chocolate.jpg",
            category: "Speciality Blends",
            badge: "INDULGENT",
            rating: 5,
            reviews_count: 125,
            available: 1,
            sold_out: 0
        },
        {
            id: 10,
            name: "Alphonso Mango Rose",
            price: 189,
            description: "Sun-soaked Ratnagiri Alphonso mango nectar harmonized with chilled rose whole milk.",
            image: "images/Mango Rose Milk.jpg",
            category: "Speciality Blends",
            badge: "SUMMER SPECIAL",
            rating: 5,
            reviews_count: 172,
            available: 1,
            sold_out: 0
        }
    ];

    /* ==========================================================================
       CART COUNT & TOAST
       ========================================================================== */
    function updateCartCount() {
        const totalItems = cart.reduce((sum, item) => sum + (item.quantity || 1), 0);
        if (cartCountBadge) {
            cartCountBadge.textContent = totalItems;
        }
    }

    function showToast(name) {
        if (!cartToast || !toastProductName) return;
        toastProductName.textContent = name;
        cartToast.classList.add("show");
        setTimeout(() => {
            cartToast.classList.remove("show");
        }, 2200);
    }

    /* ==========================================================================
       LOAD PRODUCTS (API + RESILIENT FALLBACK)
       ========================================================================== */
    async function loadCatalogue() {
        try {
            if (window.royalApi) {
                const res = await window.royalApi.get("/api/products");
                if (res.ok && res.data && res.data.success && Array.isArray(res.data.products) && res.data.products.length >= 6) {
                    allProducts = res.data.products;
                } else {
                    allProducts = fallbackProducts;
                }
            } else {
                allProducts = fallbackProducts;
            }
        } catch (err) {
            console.warn("Using luxury catalogue seed:", err);
            allProducts = fallbackProducts;
        }

        renderCatalogue();
    }

    /* ==========================================================================
       RENDER CATALOGUE SECTIONS
       ========================================================================== */
    function createProductCardHtml(p, isSpeciality = false) {
        const isSoldOut = p.sold_out === 1 || p.available === 0;
        const badgeText = isSoldOut ? "SOLD OUT" : (p.badge || "ROYAL SELECTION");
        const badgeClass = isSoldOut ? "card-badge sold-out" : (isSpeciality ? "card-badge gold" : "card-badge");
        const cardExtraClass = isSpeciality ? "product-card card-speciality" : "product-card";

        return `
            <article class="${cardExtraClass}${isSoldOut ? ' is-sold-out' : ''}" id="prod-${p.id}">
                <div class="product-img-box">
                    <span class="${badgeClass}">${badgeText}</span>
                    <img src="${p.image}" alt="${p.name}" loading="lazy" onerror="this.src='images/Royal Rose Milk.jpg'">
                </div>

                <div class="product-details">
                    <span class="product-category-label">${p.category || (isSpeciality ? 'Speciality Blend' : 'Classic Collection')}</span>
                    
                    <div class="product-rating">
                        ★★★★★
                        <span>(${p.reviews_count || 120})</span>
                    </div>

                    <h3 class="product-title">${p.name}</h3>

                    <p class="product-description">${p.description}</p>

                    <div class="product-bottom-row">
                        <div class="product-price-tag">₹${p.price}</div>
                        <span style="font-size: 11px; color: var(--color-gold); letter-spacing: 1px; text-transform: uppercase;">Chilled 250ml</span>
                    </div>

                    <div class="product-actions-group">
                        ${isSoldOut ? `
                            <button class="btn-card-cart btn-disabled" type="button" disabled>Sold Out</button>
                            <button class="btn-card-book btn-disabled" type="button" disabled>Unavailable</button>
                        ` : `
                            <button class="btn-card-cart add-cart-action" type="button" data-name="${p.name}" data-price="${p.price}" data-id="${p.id}" data-img="${p.image}">
                                Add To Cart
                            </button>
                            <button class="btn-card-book book-now-action" type="button" data-name="${p.name}" data-price="${p.price}" data-id="${p.id}" data-img="${p.image}">
                                Book Now
                            </button>
                        `}
                    </div>
                </div>
            </article>
        `;
    }

    function renderCatalogue() {
        if (!classicGrid || !specialityGrid) return;

        // Filter products based on search query
        const matchesQuery = (p) => {
            if (!searchQuery) return true;
            const q = searchQuery.toLowerCase();
            return p.name.toLowerCase().includes(q) ||
                   (p.description && p.description.toLowerCase().includes(q)) ||
                   (p.ingredients && p.ingredients.toLowerCase().includes(q)) ||
                   (p.badge && p.badge.toLowerCase().includes(q));
        };

        const classicProducts = allProducts.filter(p => {
            const isClassic = (p.category && p.category.toLowerCase().includes("classic")) ||
                              (!p.category && (p.name.includes("Classic") || p.name.includes("Signature") || p.name.includes("Strawberry") || p.name.includes("Cardamom")));
            return isClassic && matchesQuery(p);
        });

        const specialityProducts = allProducts.filter(p => {
            const isSpeciality = (p.category && p.category.toLowerCase().includes("speciality")) ||
                                 (!p.category && (p.name.includes("Saffron") || p.name.includes("Pistachio") || p.name.includes("Almond") || p.name.includes("Coconut") || p.name.includes("Cocoa") || p.name.includes("Mango") || p.name.includes("Chocolate")));
            return isSpeciality && matchesQuery(p);
        });

        // Toggle sections according to active category tab
        if (activeFilter === "classic") {
            classicGroup.classList.remove("hidden");
            specialityGroup.classList.add("hidden");
        } else if (activeFilter === "speciality") {
            classicGroup.classList.add("hidden");
            specialityGroup.classList.remove("hidden");
        } else {
            classicGroup.classList.remove("hidden");
            specialityGroup.classList.remove("hidden");
        }

        // Render Grids
        classicGrid.innerHTML = classicProducts.map(p => createProductCardHtml(p, false)).join("");
        specialityGrid.innerHTML = specialityProducts.map(p => createProductCardHtml(p, true)).join("");

        // No Results State
        const totalMatches = (activeFilter === "classic" ? classicProducts.length :
                             activeFilter === "speciality" ? specialityProducts.length :
                             classicProducts.length + specialityProducts.length);

        if (totalMatches === 0) {
            if (noResultsMsg) noResultsMsg.style.display = "block";
        } else {
            if (noResultsMsg) noResultsMsg.style.display = "none";
        }

        attachCardEvents();
    }

    /* ==========================================================================
       CARD BUTTON ACTIONS
       ========================================================================== */
    function attachCardEvents() {
        // Add to Cart
        document.querySelectorAll(".add-cart-action").forEach(btn => {
            btn.addEventListener("click", () => {
                const name = btn.dataset.name;
                const price = Number(btn.dataset.price);

                const existing = cart.find(item => item.name === name);
                if (existing) {
                    existing.quantity = (existing.quantity || 1) + 1;
                } else {
                    cart.push({ name: name, price: price, quantity: 1, image: btn.dataset.img || "" });
                }

                localStorage.setItem("royalCart", JSON.stringify(cart));
                updateCartCount();
                showToast(name);

                // Button visual feedback
                const origText = btn.textContent;
                btn.textContent = "✓ Added";
                btn.style.background = "var(--color-gold)";
                btn.style.color = "var(--color-bg-primary)";

                setTimeout(() => {
                    btn.textContent = origText;
                    btn.style.background = "";
                    btn.style.color = "";
                }, 1000);
            });
        });

        // Book Now (Direct Checkout Flow)
        document.querySelectorAll(".book-now-action").forEach(btn => {
            btn.addEventListener("click", () => {
                const product = {
                    name: btn.dataset.name,
                    price: Number(btn.dataset.price),
                    quantity: 1,
                    image: btn.dataset.img || ""
                };

                localStorage.setItem("royalDirectBooking", JSON.stringify(product));
                window.location.href = "booking.html";
            });
        });
    }

    /* ==========================================================================
       FILTER PILLS & SEARCH
       ========================================================================== */
    filterButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            filterButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            activeFilter = btn.dataset.filter || "all";
            renderCatalogue();
        });
    });

    if (searchInput) {
        searchInput.addEventListener("input", (e) => {
            searchQuery = e.target.value.trim();
            renderCatalogue();
        });
    }

    // Direct cart navigation
    const cartButton = document.getElementById("cartButton");
    if (cartButton) {
        cartButton.addEventListener("click", () => {
            window.location.href = "cart.html";
        });
    }

    // Initialize
    updateCartCount();
    loadCatalogue();
});