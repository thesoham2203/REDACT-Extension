document.addEventListener('DOMContentLoaded', () => {
    const toggleModeButton = document.getElementById('toggle-mode');
    const carouselTrack = document.querySelector('.carousel-track');
    const steps = document.querySelectorAll('.step');
    const nextArrow = document.getElementById('next-arrow');
    const prevArrow = document.getElementById('prev-arrow');
    const submitButton = document.getElementById('submit-button');
    const status = document.getElementById('status');

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

    // Redact and download logic
    submitButton.addEventListener('click', async () => {
        const fileInput = document.getElementById('file-input');
        const redactionType = document.getElementById('redaction-type').value;
        const redactionLevel = document.getElementById('redaction-level').value;

        if (!fileInput.files.length) {
            status.textContent = "Please select a file.";
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('redaction_type', redactionType);
        formData.append('redaction_level', redactionLevel);

        status.textContent = "Processing…";

        try {
            const response = await fetch('http://127.0.0.1:8000/redact', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}`);
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'redacted_' + fileInput.files[0].name;
            a.click();
            window.URL.revokeObjectURL(url);

            status.textContent = "✅ File redacted and downloaded!";
        } catch (error) {
            console.error(error);
            status.textContent = "❌ Error during redaction.";
        }
    });
});
