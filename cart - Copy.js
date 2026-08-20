document.addEventListener("DOMContentLoaded", () => {

    let cart =
        JSON.parse(
            localStorage.getItem("royalCart")
        ) || [];


    const cartItems =
        document.getElementById("cartItems");

    const emptyCart =
        document.getElementById("emptyCart");

    const itemCount =
        document.getElementById("itemCount");

    const subtotal =
        document.getElementById("subtotal");

    const delivery =
        document.getElementById("delivery");

    const grandTotal =
        document.getElementById("grandTotal");

    const checkoutBtn =
        document.getElementById("checkoutBtn");


    /* =========================
       PRODUCT EMOJIS
    ========================= */

    const productIcons = {

        "Classic Rose Milk": "🌹",

        "Strawberry Rose": "🍓🌹",

        "Royal Rose Milk": "✨🌹",

        "Rose Coconut Milk": "🥥🌹",

        "Rose Chocolate": "🍫🌹",

        "Mango Rose Milk": "🥭🌹"

    };


    /* =========================
       SAVE CART
    ========================= */

    function saveCart() {

        localStorage.setItem(
            "royalCart",
            JSON.stringify(cart)
        );
    }


    /* =========================
       RENDER CART
    ========================= */

    function renderCart() {

        cartItems.innerHTML = "";

        if (cart.length === 0) {

            emptyCart.classList.add("show");

            itemCount.textContent =
                "0 items";

            subtotal.textContent =
                "₹0";

            delivery.textContent =
                "₹0";

            grandTotal.textContent =
                "₹0";

            return;
        }


        emptyCart.classList.remove("show");


        let totalItems = 0;

        let totalPrice = 0;


        cart.forEach((item, index) => {

            totalItems += item.quantity;

            totalPrice +=
                item.price *
                item.quantity;


            const itemElement =
                document.createElement("div");

            itemElement.className =
                "cart-item";


            itemElement.innerHTML = `

                <div class="item-image">
                    ${productIcons[item.name] || "🌹"}
                </div>

                <div class="item-details">

                    <h3>
                        ${item.name}
                    </h3>

                    <p>
                        Premium Royal Rose Milk
                    </p>

                    <div class="item-price">
                        ₹${item.price}
                    </div>

                    <div class="quantity-box">

                        <button
                            class="minus"
                            data-index="${index}">
                            −
                        </button>

                        <span>
                            ${item.quantity}
                        </span>

                        <button
                            class="plus"
                            data-index="${index}">
                            +
                        </button>

                    </div>

                </div>


                <div class="item-right">

                    <div class="item-total">
                        ₹${item.price * item.quantity}
                    </div>

                    <button
                        class="remove-btn"
                        data-index="${index}">
                        Remove
                    </button>

                </div>

            `;


            cartItems.appendChild(itemElement);

        });


        itemCount.textContent =
            `${totalItems} item${totalItems !== 1 ? "s" : ""}`;


        subtotal.textContent =
            `₹${totalPrice}`;


        const deliveryCharge =
            totalPrice > 0 ? 50 : 0;


        delivery.textContent =
            `₹${deliveryCharge}`;


        grandTotal.textContent =
            `₹${totalPrice + deliveryCharge}`;


        attachButtons();
    }


    /* =========================
       BUTTONS
    ========================= */

    function attachButtons() {


        document
            .querySelectorAll(".plus")
            .forEach(button => {

                button.addEventListener(
                    "click",
                    () => {

                        const index =
                            Number(
                                button.dataset.index
                            );

                        cart[index].quantity++;

                        saveCart();

                        renderCart();

                    }
                );

            });


        document
            .querySelectorAll(".minus")
            .forEach(button => {

                button.addEventListener(
                    "click",
                    () => {

                        const index =
                            Number(
                                button.dataset.index
                            );

                        if (
                            cart[index].quantity > 1
                        ) {

                            cart[index].quantity--;

                        } else {

                            cart.splice(index, 1);

                        }

                        saveCart();

                        renderCart();

                    }
                );

            });


        document
            .querySelectorAll(".remove-btn")
            .forEach(button => {

                button.addEventListener(
                    "click",
                    () => {

                        const index =
                            Number(
                                button.dataset.index
                            );

                        const item =
                            cart[index];

                        cart.splice(index, 1);

                        saveCart();

                        renderCart();

                    }
                );

            });

    }


    /* =========================
       CHECKOUT
    ========================= */

    checkoutBtn.addEventListener(
        "click",
        () => {

            if (cart.length === 0) {

                alert(
                    "Your Royal Cart is empty 🌹"
                );

                return;
            }


            localStorage.setItem(
                "royalBookingCart",
                JSON.stringify(cart)
            );


            window.location.href =
                "booking.html";

        }
    );


    /* =========================
       PETALS
    ========================= */

    function createPetal() {

        const petal =
            document.createElement("span");

        petal.className = "petal";

        petal.textContent =
            Math.random() > .5
                ? "🌸"
                : "🌹";


        petal.style.left =
            Math.random() * 100 + "%";


        petal.style.fontSize =
            (10 + Math.random() * 14)
            + "px";


        petal.style.opacity =
            .2 + Math.random() * .5;


        petal.style.animationDuration =
            (6 + Math.random() * 6)
            + "s";


        document.body.appendChild(
            petal
        );


        setTimeout(() => {

            petal.remove();

        }, 14000);

    }


    setInterval(
        createPetal,
        1000
    );


    /* INITIAL */

    renderCart();

});