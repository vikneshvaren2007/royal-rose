document.addEventListener("DOMContentLoaded", () => {

    /* =========================
       CART
    ========================= */

    let cart = JSON.parse(localStorage.getItem("royalCart")) || [];

    const cartCount = document.getElementById("cartCount");
    const cartToast = document.getElementById("cartToast");
    const toastProduct = document.getElementById("toastProduct");


    function updateCartCount() {

        const totalItems = cart.reduce(
            (total, item) => total + item.quantity,
            0
        );

        cartCount.textContent = totalItems;
    }


    function showToast(name) {

        toastProduct.textContent = name;

        cartToast.classList.add("show");

        setTimeout(() => {
            cartToast.classList.remove("show");
        }, 2200);
    }


    document.querySelectorAll(".add-cart").forEach(button => {

        button.addEventListener("click", () => {

            const name = button.dataset.name;
            const price = Number(button.dataset.price);

            const existingProduct = cart.find(
                item => item.name === name
            );

            if (existingProduct) {

                existingProduct.quantity++;

            } else {

                cart.push({
                    name: name,
                    price: price,
                    quantity: 1
                });

            }

            localStorage.setItem(
                "royalCart",
                JSON.stringify(cart)
            );

            updateCartCount();

            showToast(name);


            /* Button animation */

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


    /* =========================
       BOOK NOW
    ========================= */

    document.querySelectorAll(".book-now").forEach(button => {

        button.addEventListener("click", () => {

            const product = {
                name: button.dataset.name,
                price: Number(button.dataset.price),
                quantity: 1
            };

            localStorage.setItem(
                "royalDirectBooking",
                JSON.stringify(product)
            );

            window.location.href = "booking.html";

        });

    });


    /* =========================
       CART BUTTON
    ========================= */

    document.getElementById("cartButton")
        .addEventListener("click", () => {

            window.location.href = "cart.html";

        });


    /* =========================
       ROSE PETALS
    ========================= */

    const petalsContainer =
        document.getElementById("petals");


    function createPetal() {

        const petal = document.createElement("span");

        petal.className = "petal";

        petal.textContent =
            Math.random() > .5 ? "🌸" : "🌹";

        petal.style.left =
            Math.random() * 100 + "%";

        petal.style.fontSize =
            (10 + Math.random() * 15) + "px";

        petal.style.animationDuration =
            (6 + Math.random() * 7) + "s";

        petal.style.opacity =
            .2 + Math.random() * .5;

        petalsContainer.appendChild(petal);

        setTimeout(() => {
            petal.remove();
        }, 14000);
    }


    setInterval(createPetal, 900);


    /* Initial count */

    updateCartCount();

});