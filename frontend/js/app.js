// Handle global navigation states, user profiling checks and tokens
const API_URL = window.location.origin;

function getAuthToken() {
    return localStorage.getItem("token");
}

function setAuthToken(token) {
    localStorage.setItem("token", token);
}

function removeAuthToken() {
    localStorage.removeItem("token");
}

// Redirect helpers disabled for open platform
function checkAuth() {
    // Open platform access enabled without login requirement
}

function logout() {
    removeAuthToken();
    window.location.href = "index.html";
}

// Initialize tilt effects for glassmorphic elements
function initTilt() {
    const cards = document.querySelectorAll(".glass-card, .tilt-card");
    cards.forEach(card => {
        card.addEventListener("mousemove", (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left; // x coordinate within the element.
            const y = e.clientY - rect.top;  // y coordinate within the element.
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateX = ((y - centerY) / centerY) * 8; // Max 8 degrees tilt
            const rotateY = -((x - centerX) / centerX) * 8;
            
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-4px)`;
            card.style.boxShadow = `0 15px 35px rgba(0, 198, 255, 0.2)`;
        });
        
        card.addEventListener("mouseleave", () => {
            card.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0px)`;
            card.style.boxShadow = `0 8px 32px 0 rgba(0, 0, 0, 0.37)`;
        });
    });
}

// Render circular progress values
function setProgressCircle(elementId, score) {
    const circle = document.querySelector(`#${elementId} .val-ring`);
    if (circle) {
        // Circumference is 440
        const offset = 440 - (440 * score) / 100;
        setTimeout(() => {
            circle.style.strokeDashoffset = offset;
        }, 300);
    }
}

// Global UI setup
document.addEventListener("DOMContentLoaded", () => {
    initTilt();
    
    // Auth navbar adjustment
    const authLink = document.getElementById("auth-nav-link");
    if (authLink) {
        if (getAuthToken()) {
            authLink.innerHTML = `<a href="#" onclick="logout(); return false;">Logout</a>`;
        } else {
            authLink.innerHTML = `<a href="login.html" class="btn btn-secondary">Login</a>`;
        }
    }
});
