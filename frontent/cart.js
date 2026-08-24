/**
 * ROYAL ROSE MILK — LUXURY CART CONTROLLER
 * Handles item quantity adjustments, subtotal & delivery calculation,
 * local storage persistence, and transition to booking checkout.
 */

document.addEventListener("DOMContentLoaded", () => {
    let cart = JSON.parse(localStorage.getItem("royalCart")) || [];

    const cartItemsContainer = document.getElementById("cartItems");
    const emptyCartBox = document.getElementById("emptyCart");
    const itemCountText = document.getElementById("itemCount");
    const subtotalText = document.getElementById("subtotal");
    const deliveryText = document.getElementById("delivery");
    const grandTotalText = document.getElementById("grandTotal");
    const checkoutBtn = document.getElementById("checkoutBtn");

    const productIcons = {
        // Classic Collection
        "Royal Rose Classic": "🌹",
        "Classic Rose Milk": "🌹",
        "Royal Rose Signature": "👑🌹",
        "Royal Rose Milk": "👑🌹",
        "Strawberry Rose Bliss": "🍓🌹",
        "Strawberry Rose": "🍓🌹",
        "Rose Cardamom Royale": "✨🌹",
        "Cardamom Rose Milk": "✨🌹",

        // Speciality Blends
        "Royal Kashmiri Saffron Elixir": "🏵️🌹",
        "Royal Pistachio Velvet": "🥜🌹",
        "Pistachio Rose Milk": "🥜🌹",
        "Rose Badam Almond Cream": "🌰🌹",
        "Almond Rose Milk": "🌰🌹",
        "Tender Coconut Rose": "🥥🌹",
        "Rose Coconut Milk": "🥥🌹",
        "Dark Cocoa Rose Noir": "🍫🌹",
        "Rose Chocolate": "🍫🌹",
        "Alphonso Mango Rose": "🥭🌹",
        "Mango Rose Milk": "🥭🌹"
    };

    function saveCart() {
        localStorage.setItem("royalCart", JSON.stringify(cart));
    }

    function renderCart() {
        if (!cartItemsContainer) return;
        cartItemsContainer.innerHTML = "";

        if (cart.length === 0) {
            if (emptyCartBox) emptyCartBox.classList.add("show");
            if (itemCountText) itemCountText.textContent = "0 items";
            if (subtotalText) subtotalText.textContent = "₹0";
            if (deliveryText) deliveryText.textContent = "₹0";
            if (grandTotalText) grandTotalText.textContent = "₹0";
            return;
        }

        if (emptyCartBox) emptyCartBox.classList.remove("show");

        let totalItems = 0;
        let totalPrice = 0;

        cart.forEach((item, index) => {
            const qty = item.quantity || 1;
            totalItems += qty;
            const itemSubtotal = item.price * qty;
            totalPrice += itemSubtotal;

            const row = document.createElement("div");
            row.className = "cart-item-row";

            row.innerHTML = `
                <div class="cart-item-icon-box">
                    ${productIcons[item.name] || "🌹"}
                </div>

                <div class="cart-item-info">
                    <h3>${item.name}</h3>
                    <p class="cart-item-subtitle">Artisanal Rose Flavored Milk • 250ml</p>
                    <div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
                        <span class="cart-item-unit-price">₹${item.price} each</span>
                        <div class="quantity-control">
                            <button class="qty-btn btn-minus" data-index="${index}" aria-label="Decrease quantity">−</button>
                            <span class="qty-value">${qty}</span>
                            <button class="qty-btn btn-plus" data-index="${index}" aria-label="Increase quantity">+</button>
                        </div>
                    </div>
                </div>

                <div class="cart-item-actions">
                    <div class="cart-item-total-price">₹${itemSubtotal}</div>
                    <button class="btn-remove-item" data-index="${index}">Remove</button>
                </div>
            `;

            cartItemsContainer.appendChild(row);
        });

        if (itemCountText) {
            itemCountText.textContent = `${totalItems} item${totalItems !== 1 ? "s" : ""}`;
        }

        if (subtotalText) {
            subtotalText.textContent = `₹${totalPrice}`;
        }

        const deliveryCharge = totalPrice > 0 ? 0 : 0; // Royal complimentary promotion
        if (deliveryText) {
            deliveryText.textContent = "FREE";
        }

        if (grandTotalText) {
            grandTotalText.textContent = `₹${totalPrice + deliveryCharge}`;
        }

        attachEventListeners();
    }

    function attachEventListeners() {
        // Increase Qty
        document.querySelectorAll(".btn-plus").forEach(btn => {
            btn.addEventListener("click", () => {
                const idx = Number(btn.dataset.index);
                cart[idx].quantity = (cart[idx].quantity || 1) + 1;
                saveCart();
                renderCart();
            });
        });

        // Decrease Qty
        document.querySelectorAll(".btn-minus").forEach(btn => {
            btn.addEventListener("click", () => {
                const idx = Number(btn.dataset.index);
                if ((cart[idx].quantity || 1) > 1) {
                    cart[idx].quantity--;
                } else {
                    cart.splice(idx, 1);
                }
                saveCart();
                renderCart();
            });
        });

        // Remove Item
        document.querySelectorAll(".btn-remove-item").forEach(btn => {
            btn.addEventListener("click", () => {
                const idx = Number(btn.dataset.index);
                cart.splice(idx, 1);
                saveCart();
                renderCart();
            });
        });
    }

    // Checkout button handler
    if (checkoutBtn) {
        checkoutBtn.addEventListener("click", () => {
            if (cart.length === 0) {
                alert("Your Royal Cart is currently empty. Please explore our collection to add delicious rose milk.");
                return;
            }

            localStorage.setItem("royalBookingCart", JSON.stringify(cart));
            window.location.href = "booking.html";
        });
    }

    renderCart();
});