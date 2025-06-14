// frontend/js/nav-script.js
document.addEventListener('DOMContentLoaded', () => {
    const menuToggle = document.getElementById('menu-toggle');
    const navLinksUl = document.getElementById('nav-links'); // Target the UL

    // --- Mobile Menu Toggle ---
    if (menuToggle && navLinksUl) {
        menuToggle.addEventListener('click', () => {
            navLinksUl.classList.toggle('active');
            menuToggle.classList.toggle('active');
            // Update ARIA attribute for accessibility
            const isExpanded = menuToggle.getAttribute('aria-expanded') === 'true' || false;
            menuToggle.setAttribute('aria-expanded', !isExpanded);

            // Prevent body scroll when menu is open (Optional)
            // document.body.classList.toggle('no-scroll', navLinksUl.classList.contains('active'));
        });

        // Close menu when a link is clicked (for single-page navigation or UX)
        navLinksUl.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                if (navLinksUl.classList.contains('active')) {
                    navLinksUl.classList.remove('active');
                    menuToggle.classList.remove('active');
                    menuToggle.setAttribute('aria-expanded', 'false');
                    // document.body.classList.remove('no-scroll'); // If using no-scroll
                }
            });
        });
    }


    // --- Active Navigation Link Styling ---
    // Get filename from URL path: e.g. "index.html", "select-issue.html"
    // Handles cases like /path/ or /path/index.html
    const pathSegments = window.location.pathname.split('/').filter(segment => segment !== '');
    const currentPage = pathSegments.length > 0 ? pathSegments.pop() : 'index.html';
    if (currentPage === '') currentPage = 'index.html'; // Handle root path case correctly

    const navLinks = document.querySelectorAll('.navbar .nav-links .nav-link');

    navLinks.forEach(link => {
        const linkHref = link.getAttribute('href');
        if (linkHref) {
            const linkPage = linkHref.split('/').pop();
            // Check if the link's target matches the current page file name
            if (linkPage === currentPage) {
                link.classList.add('active-page');
            }
            // Special case for the "Home" link if the current page is the root index.html
            if (currentPage === 'index.html' && (linkHref === '/' || linkHref === 'index.html' || linkHref === './')) {
                link.classList.add('active-page');
            }
        }
    });

    // Optional: Header background change on scroll - Removed from initial CSS, add JS if needed
    // const header = document.querySelector('.main-header');
    // if (header) {
    //     window.addEventListener('scroll', () => {
    //         if (window.scrollY > 50) { // Add 'scrolled' class after 50px scroll
    //             header.classList.add('scrolled');
    //         } else {
    //             header.classList.remove('scrolled');
    //         }
    //     });
    // }
});