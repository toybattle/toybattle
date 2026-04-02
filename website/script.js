/* ============================================
   TOY BATTLE — Landing Page Scripts
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {

    // ---- Particle System ----
    initParticles();

    // ---- Navbar Scroll Effect ----
    initNavbar();

    // ---- Mobile Menu ----
    initMobileMenu();

    // ---- Stats Counter Animation ----
    initStatsCounter();

    // ---- Feature Cards Scroll Reveal ----
    initScrollReveal();

    // ---- Gallery ----
    initGallery();

    // ---- Smooth Scroll ----
    initSmoothScroll();
});


/* ============================================
   PARTICLE SYSTEM
   ============================================ */
function initParticles() {
    const canvas = document.getElementById('particles-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let particles = [];
    let animFrameId;
    const PARTICLE_COUNT = 60;

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }

    resize();
    window.addEventListener('resize', resize);

    class Particle {
        constructor() {
            this.reset();
        }

        reset() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 2 + 0.5;
            this.speedX = (Math.random() - 0.5) * 0.4;
            this.speedY = (Math.random() - 0.5) * 0.4;
            this.opacity = Math.random() * 0.4 + 0.1;
            this.hue = Math.random() > 0.5 ? 260 : 340; // purple or pink
        }

        update() {
            this.x += this.speedX;
            this.y += this.speedY;

            if (this.x < 0 || this.x > canvas.width) this.speedX *= -1;
            if (this.y < 0 || this.y > canvas.height) this.speedY *= -1;
        }

        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = `hsla(${this.hue}, 70%, 70%, ${this.opacity})`;
            ctx.fill();
        }
    }

    // Create particles
    for (let i = 0; i < PARTICLE_COUNT; i++) {
        particles.push(new Particle());
    }

    function connectParticles() {
        const maxDist = 120;
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < maxDist) {
                    const opacity = (1 - dist / maxDist) * 0.08;
                    ctx.beginPath();
                    ctx.strokeStyle = `rgba(108, 92, 231, ${opacity})`;
                    ctx.lineWidth = 0.5;
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.stroke();
                }
            }
        }
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        particles.forEach(p => {
            p.update();
            p.draw();
        });

        connectParticles();
        animFrameId = requestAnimationFrame(animate);
    }

    animate();
}


/* ============================================
   NAVBAR
   ============================================ */
function initNavbar() {
    const navbar = document.getElementById('navbar');
    if (!navbar) return;

    let lastScroll = 0;

    function onScroll() {
        const scrollY = window.scrollY;

        if (scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }

        lastScroll = scrollY;
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll(); // initial check
}


/* ============================================
   MOBILE MENU
   ============================================ */
function initMobileMenu() {
    const toggle = document.getElementById('nav-toggle');
    const links = document.getElementById('nav-links');
    if (!toggle || !links) return;

    toggle.addEventListener('click', () => {
        toggle.classList.toggle('active');
        links.classList.toggle('open');
        document.body.style.overflow = links.classList.contains('open') ? 'hidden' : '';
    });

    // Close menu when clicking a link
    links.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            toggle.classList.remove('active');
            links.classList.remove('open');
            document.body.style.overflow = '';
        });
    });
}


/* ============================================
   STATS COUNTER
   ============================================ */
function initStatsCounter() {
    const statNumbers = document.querySelectorAll('.stat-number');
    if (!statNumbers.length) return;

    let hasAnimated = false;

    function animateStats() {
        if (hasAnimated) return;

        const statsSection = document.querySelector('.hero-stats');
        if (!statsSection) return;

        const rect = statsSection.getBoundingClientRect();
        if (rect.top > window.innerHeight || rect.bottom < 0) return;

        hasAnimated = true;

        statNumbers.forEach(el => {
            const target = parseFloat(el.dataset.target);
            const isDecimal = el.classList.contains('stat-rating-val');
            const duration = 2000;
            const startTime = performance.now();

            function updateCount(now) {
                const elapsed = now - startTime;
                const progress = Math.min(elapsed / duration, 1);
                // Ease out cubic
                const eased = 1 - Math.pow(1 - progress, 3);
                const current = target * eased;

                if (isDecimal) {
                    el.textContent = current.toFixed(1);
                } else {
                    el.textContent = Math.floor(current).toLocaleString('fr-FR');
                }

                if (progress < 1) {
                    requestAnimationFrame(updateCount);
                } else {
                    if (isDecimal) {
                        el.textContent = target.toFixed(1);
                    } else {
                        el.textContent = Math.floor(target).toLocaleString('fr-FR');
                    }
                }
            }

            requestAnimationFrame(updateCount);
        });
    }

    // Start animating after hero animations are done
    setTimeout(() => {
        animateStats();
        window.addEventListener('scroll', animateStats, { passive: true });
    }, 1500);
}


/* ============================================
   SCROLL REVEAL
   ============================================ */
function initScrollReveal() {
    const cards = document.querySelectorAll('.feature-card');
    if (!cards.length) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, i) => {
            if (entry.isIntersecting) {
                // Stagger the animations
                const card = entry.target;
                const index = Array.from(cards).indexOf(card);
                setTimeout(() => {
                    card.classList.add('visible');
                }, index * 100);
                observer.unobserve(card);
            }
        });
    }, {
        threshold: 0.15,
        rootMargin: '0px 0px -50px 0px'
    });

    cards.forEach(card => observer.observe(card));

    // Also reveal other sections
    const revealElements = document.querySelectorAll('.gallery-showcase, .specs-grid, .download-box');
    const sectionObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                sectionObserver.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -30px 0px'
    });

    revealElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.7s ease, transform 0.7s ease';
        sectionObserver.observe(el);
    });
}


/* ============================================
   GALLERY
   ============================================ */
function initGallery() {
    const thumbs = document.querySelectorAll('.gallery-thumb');
    const mainImg = document.getElementById('gallery-main-img');
    const caption = document.getElementById('gallery-caption');
    if (!thumbs.length || !mainImg || !caption) return;

    thumbs.forEach(thumb => {
        thumb.addEventListener('click', () => {
            const imgSrc = thumb.dataset.img;
            const capText = thumb.dataset.caption;

            // Remove active from all thumbs
            thumbs.forEach(t => t.classList.remove('active'));
            thumb.classList.add('active');

            // Fade transition
            mainImg.style.opacity = '0';
            mainImg.style.transform = 'scale(1.02)';

            setTimeout(() => {
                mainImg.src = imgSrc;
                caption.textContent = capText;

                mainImg.style.opacity = '1';
                mainImg.style.transform = 'scale(1)';
            }, 300);
        });
    });

    // Add transition styles to main image
    mainImg.style.transition = 'opacity 0.3s ease, transform 0.5s ease';
}


/* ============================================
   SMOOTH SCROLL
   ============================================ */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', (e) => {
            const targetId = anchor.getAttribute('href');
            if (targetId === '#') return;

            const targetEl = document.querySelector(targetId);
            if (!targetEl) return;

            e.preventDefault();

            const navHeight = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--nav-height')) || 72;
            const targetPos = targetEl.getBoundingClientRect().top + window.scrollY - navHeight;

            window.scrollTo({
                top: targetPos,
                behavior: 'smooth'
            });
        });
    });
}
