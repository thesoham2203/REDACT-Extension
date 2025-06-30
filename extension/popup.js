document.addEventListener('DOMContentLoaded', () => {
    const toggleModeButton = document.getElementById('toggle-mode');
    const carouselTrack = document.querySelector('.carousel-track');
    const steps = document.querySelectorAll('.step');
    const nextArrow = document.getElementById('next-arrow');
    const prevArrow = document.getElementById('prev-arrow');

    let currentStep = 0;

    // Toggle Light/Dark Mode
    toggleModeButton.addEventListener('click', () => {
        document.body.classList.toggle('light-mode');
        document.body.classList.toggle('dark-mode');
        toggleModeButton.textContent = document.body.classList.contains('dark-mode') ? '☀️' : '🌙';
    });

    // Update Carousel
    function updateCarousel() {
        const translateX = -currentStep * 100;
        carouselTrack.style.transform = `translateX(${translateX}%)`;
    }

    // Next Slide
    nextArrow.addEventListener('click', () => {
        if (currentStep < steps.length - 1) {
            currentStep++;
            updateCarousel();
        }
    });

    // Previous Slide
    prevArrow.addEventListener('click', () => {
        if (currentStep > 0) {
            currentStep--;
            updateCarousel();
        }
    });
});


