/**
 * ROYAL ROSE MILK — CINEMATIC INTERACTIVE ENGINE
 * Features:
 * 1. Lightweight Canvas Particle Engine (Floating Damask Petals & Gold Dust)
 * 2. Brand Intro & Loading Screen Controller
 * 3. Minimal Desktop Custom Cursor Follower
 * 4. Header Glassmorphism & Mobile Drawer Navigation
 * 5. IntersectionObserver Scroll Storytelling Reveal
 * 6. Global Cart Counter & Newsletter Management
 */

document.addEventListener("DOMContentLoaded", () => {

    /* ==========================================================================
       1. LUXURY CUSTOM CURSOR (Desktop Only)
       ========================================================================== */
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    
    if (!isTouchDevice && window.innerWidth > 991) {
        const dot = document.createElement("div");
        dot.className = "custom-cursor-dot";
        const ring = document.createElement("div");
        ring.className = "custom-cursor-ring";
        document.body.appendChild(dot);
        document.body.appendChild(ring);

        let mouseX = window.innerWidth / 2;
        let mouseY = window.innerHeight / 2;
        let ringX = mouseX;
        let ringY = mouseY;

        window.addEventListener("mousemove", (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
            dot.style.transform = `translate(${mouseX}px, ${mouseY}px) translate(-50%, -50%)`;
        });

        function animateCursor() {
            ringX += (mouseX - ringX) * 0.15;
            ringY += (mouseY - ringY) * 0.15;
            ring.style.transform = `translate(${ringX}px, ${ringY}px) translate(-50%, -50%)`;
            requestAnimationFrame(animateCursor);
        }
        animateCursor();

        // Magnetic Hover Effect
        const interactiveElements = document.querySelectorAll("a, button, input, textarea, .product-card, .method-card, .pillar-card, .ingredient-box");
        interactiveElements.forEach((el) => {
            el.addEventListener("mouseenter", () => document.body.classList.add("cursor-hover"));
            el.addEventListener("mouseleave", () => document.body.classList.remove("cursor-hover"));
        });
    }

    /* ==========================================================================
       2. CINEMATIC CANVAS PARTICLE ENGINE (Petals & Golden Dust)
       ========================================================================== */
    const canvas = document.getElementById("particlesCanvas");
    if (canvas) {
        const ctx = canvas.getContext("2d");
        let width = canvas.width = window.innerWidth;
        let height = canvas.height = window.innerHeight;

        window.addEventListener("resize", () => {
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
        });

        const isMobile = window.innerWidth < 768;
        const petalCount = isMobile ? 12 : 26;
        const dustCount = isMobile ? 20 : 45;

        // Damask Rose Petal Class
        class Petal {
            constructor() {
                this.reset();
                this.y = Math.random() * height; // initial random distribution
            }

            reset() {
                this.x = Math.random() * width;
                this.y = -20;
                this.size = 10 + Math.random() * 14;
                this.speedY = 0.8 + Math.random() * 1.4;
                this.speedX = -0.5 + Math.random() * 1.0;
                this.rotation = Math.random() * Math.PI * 2;
                this.rotationSpeed = (Math.random() - 0.5) * 0.025;
                this.opacity = 0.3 + Math.random() * 0.45;
                this.swayAngle = Math.random() * Math.PI * 2;
                this.swaySpeed = 0.02 + Math.random() * 0.02;
                this.color = Math.random() > 0.4 ? "#A63259" : "#D9608A";
            }

            update() {
                this.y += this.speedY;
                this.swayAngle += this.swaySpeed;
                this.x += this.speedX + Math.sin(this.swayAngle) * 0.6;
                this.rotation += this.rotationSpeed;

                if (this.y > height + 30 || this.x < -30 || this.x > width + 30) {
                    this.reset();
                }
            }

            draw() {
                ctx.save();
                ctx.translate(this.x, this.y);
                ctx.rotate(this.rotation);
                ctx.globalAlpha = this.opacity;

                // Draw organic petal shape
                ctx.fillStyle = this.color;
                ctx.beginPath();
                ctx.moveTo(0, -this.size);
                ctx.bezierCurveTo(this.size * 0.8, -this.size * 0.5, this.size * 0.8, this.size * 0.8, 0, this.size);
                ctx.bezierCurveTo(-this.size * 0.8, this.size * 0.8, -this.size * 0.8, -this.size * 0.5, 0, -this.size);
                ctx.fill();

                // Subtle petal inner highlight
                ctx.fillStyle = "rgba(255, 230, 240, 0.35)";
                ctx.beginPath();
                ctx.ellipse(0, -this.size * 0.2, this.size * 0.2, this.size * 0.5, 0, 0, Math.PI * 2);
                ctx.fill();

                ctx.restore();
            }
        }

        // Golden Dust Particle Class
        class GoldDust {
            constructor() {
                this.reset();
                this.y = Math.random() * height;
            }

            reset() {
                this.x = Math.random() * width;
                this.y = Math.random() * height;
                this.radius = 0.6 + Math.random() * 1.5;
                this.speedY = -0.2 - Math.random() * 0.4;
                this.speedX = (Math.random() - 0.5) * 0.3;
                this.opacity = 0.2 + Math.random() * 0.5;
                this.pulse = Math.random() * Math.PI;
            }

            update() {
                this.y += this.speedY;
                this.x += this.speedX;
                this.pulse += 0.03;
                this.currentOpacity = this.opacity * (0.6 + Math.sin(this.pulse) * 0.4);

                if (this.y < -10) this.y = height + 10;
                if (this.x < -10) this.x = width + 10;
                if (this.x > width + 10) this.x = -10;
            }

            draw() {
                ctx.save();
                ctx.globalAlpha = Math.max(0, this.currentOpacity);
                ctx.fillStyle = "#F3E5AB";
                ctx.shadowColor = "#D4AF70";
                ctx.shadowBlur = 6;
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
                ctx.fill();
                ctx.restore();
            }
        }

        const petals = Array.from({ length: petalCount }, () => new Petal());
        const dusts = Array.from({ length: dustCount }, () => new GoldDust());

        let animationFrameId;
        function renderParticles() {
            if (!document.hidden) {
                ctx.clearRect(0, 0, width, height);
                dusts.forEach(d => { d.update(); d.draw(); });
                petals.forEach(p => { p.update(); p.draw(); });
            }
            animationFrameId = requestAnimationFrame(renderParticles);
        }
        renderParticles();
    }

    /* ==========================================================================
       3. BRAND INTRO & CINEMATIC LOADER
       ========================================================================== */
    const loader = document.getElementById("royalLoader");
    const progressBar = document.getElementById("loaderProgress");
    const percentText = document.getElementById("loaderPercent");
    const heroVideo = document.getElementById("heroVideo");
    
    let isAlreadyShown = false;
    try {
        isAlreadyShown = sessionStorage.getItem("royalLoadingShown") === "true";
    } catch (e) {}

    if (loader) {
        if (isAlreadyShown) {
            // Already viewed in this session -> immediately bypass
            loader.classList.add("loader-hide");
            loader.style.display = "none";
            document.body.style.overflow = "";
            if (heroVideo) {
                heroVideo.play().catch(() => {});
            }
        } else {
            // First time in this browser session -> play brand intro
            document.body.style.overflow = "hidden";

            let progress = 0;
            const interval = setInterval(() => {
                progress += Math.floor(Math.random() * 8) + 4;
                if (progress >= 100) {
                    progress = 100;
                    clearInterval(interval);
                    
                    if (progressBar) progressBar.style.width = "100%";
                    if (percentText) percentText.textContent = "100%";

                    setTimeout(() => {
                        try {
                            sessionStorage.setItem("royalLoadingShown", "true");
                        } catch (e) {}

                        if (heroVideo) {
                            heroVideo.play().catch(() => console.log("Autoplay handled."));
                        }
                        loader.classList.add("loader-hide");
                        setTimeout(() => {
                            loader.style.display = "none";
                        }, 800);
                        document.body.style.overflow = "";
                    }, 400);
                } else {
                    if (progressBar) progressBar.style.width = progress + "%";
                    if (percentText) percentText.textContent = progress + "%";
                }
            }, 50);
        }
    }

    /* ==========================================================================
       4. NAVBAR SCROLL EFFECT & MOBILE MENU
       ========================================================================== */
    const header = document.querySelector(".site-header");
    if (header) {
        window.addEventListener("scroll", () => {
            if (window.scrollY > 30) {
                header.classList.add("scrolled");
            } else {
                header.classList.remove("scrolled");
            }
        });
    }

    const mobileToggle = document.getElementById("mobileToggle");
    const mobileDrawer = document.getElementById("mobileDrawer");

    if (mobileToggle && mobileDrawer) {
        mobileToggle.addEventListener("click", () => {
            const isOpen = mobileDrawer.classList.toggle("open");
            mobileToggle.classList.toggle("open");
            document.body.style.overflow = isOpen ? "hidden" : "";
        });

        // Close drawer on link click
        mobileDrawer.querySelectorAll("a").forEach(link => {
            link.addEventListener("click", () => {
                mobileDrawer.classList.remove("open");
                mobileToggle.classList.remove("open");
                document.body.style.overflow = "";
            });
        });
    }

    /* ==========================================================================
       5. SCROLL STORYTELLING REVEAL (IntersectionObserver)
       ========================================================================== */
    const revealElements = document.querySelectorAll(".cinematic-reveal, .cinematic-reveal-left, .cinematic-reveal-right");
    
    if (revealElements.length > 0) {
        const observerOptions = {
            threshold: 0.12,
            rootMargin: "0px 0px -40px 0px"
        };

        const revealObserver = new IntersectionObserver((entries, obs) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("visible");
                    obs.unobserve(entry.target);
                }
            });
        }, observerOptions);

        revealElements.forEach(el => revealObserver.observe(el));
    }

    /* ==========================================================================
       6. GLOBAL CART COUNTER SYNC
       ========================================================================== */
    function syncCartCount() {
        const cart = JSON.parse(localStorage.getItem("royalCart")) || [];
        const totalItems = cart.reduce((total, item) => total + (item.quantity || 1), 0);
        
        document.querySelectorAll(".nav-cart-count, #cartCount").forEach(badge => {
            badge.textContent = totalItems;
        });
    }
    syncCartCount();
    window.addEventListener("storage", syncCartCount);

    /* ==========================================================================
       7. NEWSLETTER FORM
       ========================================================================== */
    const newsletterForm = document.getElementById("newsletterForm");
    if (newsletterForm) {
        newsletterForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const emailInput = document.getElementById("newsletterEmail");
            if (emailInput && emailInput.value.trim()) {
                alert("Thank you for joining the ROYAL Circle. You will receive our exclusive releases & seasonal stories.");
                emailInput.value = "";
            }
        });
    }

    /* ==========================================================================
       8. AMBIENT MOUSE LIGHT GLOW
       ========================================================================== */
    const lightGlow = document.querySelector(".ambient-light-glow");
    if (lightGlow && !isTouchDevice) {
        window.addEventListener("mousemove", (e) => {
            lightGlow.style.transform = `translate(${e.clientX}px, ${e.clientY}px) translate(-50%, -50%)`;
        });
    }
});