document.addEventListener("DOMContentLoaded", function () {
    // Only run animations if gsap is available
    if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') {
        console.warn("GSAP or ScrollTrigger is not loaded.");
        return;
    }

    // Register GSAP ScrollTrigger
    gsap.registerPlugin(ScrollTrigger);

    // 1. Page heading: Slide down with a fade-in effect on page load
    gsap.from(".page-title, .category-main-title", {
        y: -50,
        opacity: 0,
        duration: 1,
        ease: "power3.out",
        delay: 0.1
    });

    // 2. News cards: Staggered fade-up animation
    // Group them by grid so stagger works per grid block
    const grids = document.querySelectorAll('.news-grid');
    grids.forEach(grid => {
        const cards = grid.querySelectorAll('.news-card:not(.ad-banner)');
        if (cards.length > 0) {
            gsap.from(cards, {
                scrollTrigger: {
                    trigger: grid,
                    start: "top 85%",
                    toggleActions: "play none none none"
                },
                y: 50,
                opacity: 0,
                duration: 0.8,
                stagger: 0.1,
                ease: "power2.out"
            });
        }
    });

    // 3. Section blocks: Scroll-triggered animations
    const sections = document.querySelectorAll('.editorial-section');
    sections.forEach(section => {
        // Prevent animating sections that might clash with news card inner animations if desired,
        // but typically animating the whole section wrapper slightly works well.
        gsap.from(section, {
            scrollTrigger: {
                trigger: section,
                start: "top 90%",
                toggleActions: "play none none none"
            },
            y: 30,
            opacity: 0,
            duration: 1,
            ease: "power2.out"
        });
    });

    // 4. Advertisement banner: Smooth scale or fade animation
    const adBanners = document.querySelectorAll('.ad-banner');
    adBanners.forEach(ad => {
        gsap.from(ad, {
            scrollTrigger: {
                trigger: ad,
                start: "top 85%",
                toggleActions: "play none none none"
            },
            scale: 0.95,
            opacity: 0,
            duration: 1,
            ease: "back.out(1.7)"
        });
    });

    // === ADVERTISEMENT PAGE SPECIFIC ANIMATIONS ===
    
    // Animate hero section
    const advertiseHero = document.querySelector('.advertise-hero');
    if (advertiseHero) {
        gsap.from('.advertise-hero h1', {
            y: -30,
            opacity: 0,
            duration: 1,
            ease: "power3.out"
        });
        
        gsap.from('.advertise-hero p', {
            y: 20,
            opacity: 0,
            duration: 1,
            delay: 0.2,
            ease: "power3.out"
        });
    }

    // Animate stats cards
    const statCards = document.querySelectorAll('.stat-card');
    if (statCards.length > 0) {
        gsap.from(statCards, {
            scrollTrigger: {
                trigger: '.stats-section',
                start: "top 80%",
                toggleActions: "play none none none"
            },
            y: 50,
            opacity: 0,
            duration: 0.8,
            stagger: 0.15,
            ease: "back.out(1.5)"
        });
    }

    // Animate feature cards
    const featureCards = document.querySelectorAll('.feature-card');
    if (featureCards.length > 0) {
        gsap.from(featureCards, {
            scrollTrigger: {
                trigger: '.advertise-grid',
                start: "top 80%",
                toggleActions: "play none none none"
            },
            y: 60,
            opacity: 0,
            duration: 0.8,
            stagger: 0.2,
            ease: "power2.out"
        });
    }



    // Removal of ScrollTrigger for form groups inside advertise-form-wrapper 
    // to prevent invisibility issues when displayed dynamically.
    // Staggered animation is now handled in advertise.html's selectPlan function.

    // Submit button animation is now handled along with form groups for better reliability.
    // Removed ScrollTrigger to avoid visibility issues in the dynamic form.
});
