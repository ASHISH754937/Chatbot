document.addEventListener("DOMContentLoaded", function () {
    // Enter key to send message
    const inputField = document.getElementById("user-input");
    const sendButton = document.getElementById("send-button");
    if (inputField && sendButton) {
        inputField.addEventListener("keypress", function (event) {
            if (event.key === "Enter") {
                event.preventDefault();
                sendButton.click();
            }
        });
    }

    // Logout button
    const logoutButton = document.getElementById("logout-button");
    if (logoutButton) {
        logoutButton.addEventListener("click", function(event) {
            event.preventDefault();
            window.location.href = "/logout";
        });
    }

    // Menu toggle
    const menuIcon = document.querySelector(".menu-icon");
    const navLinks = document.querySelector(".nav-links");
    if (menuIcon && navLinks) {
        menuIcon.addEventListener("click", function () {
            navLinks.classList.toggle("active");
        });
    }

    // Flash message auto-hide
    const flashMessages = document.getElementById("flash-messages");
    if (flashMessages) {
        setTimeout(() => {
            flashMessages.style.display = "none";
        }, 4000); // Hide after 4 seconds
    }
});


async function sendMessage() {
    let inputField = document.getElementById("user-input");
    let userMessage = inputField.value.trim();
    if (!userMessage) return;

    let chatBox = document.getElementById("chat-box");
    chatBox.innerHTML += `<div class="message user">You: ${userMessage}</div>`;
    inputField.value = "";

    let botMessage = document.createElement("pre"); 
    botMessage.className = "message bot";
    botMessage.innerHTML = `<strong>Bot:</strong>\n`; 
    chatBox.appendChild(botMessage);

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: userMessage })
        });

        const reader = response.body.getReader();
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            botMessage.innerHTML += new TextDecoder().decode(value);
            chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll
        }
    } catch (error) {
        botMessage.innerHTML += `<br><span style="color:red;">Error: ${error.message}</span>`;
    }
}