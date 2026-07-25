const locationSelect = document.getElementById("location");
const hero = document.getElementById("hero-carousel");

const locationMap = {
    "Whitefield": "https://example.com/image1.jpg",
    "Indira Nagar": "https://example.com/image2.jpg",
    "Electronic City": "https://example.com/image3.jpg"
};

locationSelect.addEventListener("change", function () {

    const selectedLocation = this.value;

    if (locationMap[selectedLocation]) {
        hero.style.backgroundImage =
            `url('${locationMap[selectedLocation]}')`;
    }

});