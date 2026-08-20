/**
 * ROYAL ROSE MILK — Dynamic Shopping & Collection Controller
 * Loads active products from database via /api/products, handles sold-out
 * state, cart manipulation, and direct booking redirection.
 */

document.addEventListener("DOMContentLoaded", () => {

    /* =========================
       STATE & ELEMENTS
    ========================= */
    let cart = JSON.parse(localStorage.getItem("royalCart")) || [];
    const cartCount = document.getElementById("cartCount");
    const cartToast = document.getElementById("cartToast");
    const toastProduct = document.getElementById("toastProduct");
    const productGrid = document.getElementById("productGrid");

    function updateCartCount() {
        const totalItems = cart.reduce((total, item) => total + item.quantity, 0);
        if (cartCount) cartCount.textContent = totalItems;
    }

    function showToast(name) {
        if (!cartToast || !toastProduct) return;
        toastProduct.textContent = name;
        cartToast.classList.add("show");
        setTimeout(() => {
            cartToast.classList.remove("show");
        }, 2200);
    }

    /* =========================
       DYNAMIC PRODUCT RENDERING
    ========================= */
    async function loadProducts() {
        if (!productGrid) return;

        // Display sleek loading placeholder if grid is empty
        productGrid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 60px 20px; color: #8e2346;">
                <span style="font-size: 32px; display: block; margin-bottom: 12px; animation: spin 2s linear infinite;">🍹</span>
                <p style="font-size: 16px; font-weight: 500;">Loading Royal Collection...</p>
            </div>
        `;

        try {
            const res = await window.royalApi.get("/api/products");

            if (res.ok && res.data.success && Array.isArray(res.data.products) && res.data.products.length > 0) {
                renderProductGrid(res.data.products);
            } else {
                productGrid.innerHTML = `
                    <div style="grid-column: 1 / -1; text-align: center; padding: 50px 20px; color: #8e2346;">
                        <p style="font-size: 16px;">No varieties currently available. Please check back shortly!</p>
                    </div>
                `;
            }
        } catch (err) {
            console.error("Error loading products:", err);
            productGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 50px 20px; color: #8e2346;">
                    <p style="font-size: 16px;">Unable to load catalogue at this moment.</p>
                </div>
            `;
        }
    }

    function renderProductGrid(products) {
        productGrid.innerHTML = "";

        products.forEach(p => {
            const isSoldOut = p.sold_out === 1 || p.available === 0;
            const badgeText = isSoldOut ? "SOLD OUT" : (p.badge || "ROYAL FAVOURITE");
            const badgeClass = isSoldOut ? "badge sold-out" : "badge";
            const cardClass = isSoldOut ? "product-card is-sold-out" : "product-card";

            const card = document.createElement("article");
            card.className = cardClass;
            card.id = `prod-${p.id}`;

            card.innerHTML = `
                <div class="product-image">
                    <span class="${badgeClass}">${badgeText}</span>
                    <img src="${p.image || 'images/Royal Rose Milk.jpg'}" alt="${p.name}" loading="lazy" onerror="this.src='images/Royal Rose Milk.jpg'">
                    <div class="shine"></div>
                </div>

                <div class="product-info">
                    <div class="rating">
                        ★★★★★
                        <span>(${p.reviews_count || 128})</span>
                    </div>

                    <h3>${p.name}</h3>

                    <p>${p.description || 'Smooth, creamy and beautifully infused with authentic rose essence.'}</p>

                    <div class="product-bottom">
                        <strong>₹${p.price}</strong>
                    </div>

                    <div class="product-actions">
                        ${isSoldOut ? `
                            <button class="add-cart btn-disabled" type="button" disabled title="This item is currently sold out">
                                SOLD OUT
                            </button>
                            <button class="book-now btn-disabled" type="button" disabled title="This item is currently sold out">
                                UNAVAILABLE
                            </button>
                        ` : `
                            <button class="add-cart" type="button" data-name="${p.name}" data-price="${p.price}" data-id="${p.id}">
                                Add to Cart
                            </button>
                            <button class="book-now" type="button" data-name="${p.name}" data-price="${p.price}" data-id="${p.id}">
                                Book Now
                            </button>
                        `}
                    </div>
                </div>
            `;

            productGrid.appendChild(card);
        });

        attachProductActions();
    }

    function attachProductActions() {
        // ADD TO CART
        document.querySelectorAll(".add-cart:not([disabled])").forEach(button => {
            button.addEventListener("click", () => {
                const name = button.dataset.name;
                const price = Number(button.dataset.price);

                const existing = cart.find(item => item.name === name);
                if (existing) {
                    existing.quantity++;
                } else {
                    cart.push({ name: name, price: price, quantity: 1 });
                }

                localStorage.setItem("royalCart", JSON.stringify(cart));
                updateCartCount();
                showToast(name);

                // Button feedback
                const originalText = button.textContent;
                button.textContent = "✓ Added";
                button.style.background = "#d94370";
                button.style.color = "#fff";

                setTimeout(() => {
                    button.textContent = originalText;
                    button.style.background = "";
                    button.style.color = "";
                }, 1000);
            });
        });

        // BOOK NOW
        document.querySelectorAll(".book-now:not([disabled])").forEach(button => {
            button.addEventListener("click", () => {
                const product = {
                    name: button.dataset.name,
                    price: Number(button.dataset.price),
                    quantity: 1
                };

                localStorage.setItem("royalDirectBooking", JSON.stringify(product));
                window.location.href = "booking.html";
            });
        });
    }

    /* =========================
       CART BUTTON & PETALS
    ========================= */
    const cartBtn = document.getElementById("cartButton");
    if (cartBtn) {
        cartBtn.addEventListener("click", () => {
            window.location.href = "cart.html";
        });
    }

    const petalsContainer = document.getElementById("petals");
    function createPetal() {
        if (!petalsContainer) return;
        const petal = document.createElement("span");
        petal.className = "petal";
        petal.textContent = Math.random() > .5 ? "🌸" : "🌹";
        petal.style.left = Math.random() * 100 + "%";
        petal.style.fontSize = (10 + Math.random() * 15) + "px";
        petal.style.animationDuration = (6 + Math.random() * 7) + "s";
        petal.style.opacity = .2 + Math.random() * .5;
        petalsContainer.appendChild(petal);
        setTimeout(() => { petal.remove(); }, 14000);
    }
    setInterval(createPetal, 900);

    // Initial setup
    updateCartCount();
    loadProducts();
});