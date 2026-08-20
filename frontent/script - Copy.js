document.addEventListener("DOMContentLoaded", () => {

    const heartRain = document.getElementById("heartRain");

    if (!heartRain) {
        console.log("heartRain not found");
        return;
    }

    function createHeart() {

        const heart = document.createElement("span");

        heart.classList.add("falling-heart");

        heart.textContent =
            Math.random() > 0.5 ? "♥" : "♡";

        heart.style.left =
            Math.random() * 100 + "%";

        heart.style.fontSize =
            (12 + Math.random() * 14) + "px";

        heart.style.setProperty(
            "--drift",
            (-80 + Math.random() * 160) + "px"
        );

        const duration =
            6 + Math.random() * 5;

        heart.style.animationDuration =
            duration + "s";

        heartRain.appendChild(heart);

        setTimeout(() => {
            heart.remove();
        }, duration * 1000);
    }

    // Start immediately
    for (let i = 0; i < 30; i++) {
        setTimeout(createHeart, i * 150);
    }

    // Continue forever
    setInterval(createHeart, 300);

});
/* =========================================================
   CINEMATIC INTRO
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    const intro = document.getElementById("cinematic-intro");

    const video = document.getElementById("hero-video");


    /* VIDEO FINISHED */

    video.addEventListener("ended", function () {

        intro.classList.add("hide");

    });

});