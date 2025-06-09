// Custom JavaScript for Flask App

document.addEventListener('DOMContentLoaded', function() {
  // Enable tooltips
  var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl)
  });
  
  // Enable popovers
  var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
  var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl)
  });

  // Flash message auto-close after 5 seconds
  setTimeout(function() {
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
      var bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    });
  }, 5000);

  // This is for Chat
    document.getElementById("chat-header").addEventListener("click", function() {
      let chatBox = document.getElementById("chat-container");
      chatBox.style.display = (chatBox.style.display === "none" || chatBox.style.display === "") ? "block" : "none";
  });

  // Function to handle sending messages
  async function sendMessage() {
      let userInput = document.getElementById("chat-input").value;
      if (userInput.trim() === "") return;

      let chatBody = document.getElementById("chat-body");
      chatBody.innerHTML += `<div><b>You:</b> ${userInput}</div>`;
      
      // Show loading spinner
      let loadingDiv = document.createElement("div");
      loadingDiv.id = "loading-spinner";
      loadingDiv.innerHTML = `<div class="spinner-border text-primary spinner-border-sm" role="status">
                                <span class="visually-hidden">Loading...</span>
                             </div> <span>Thinking...</span>`;
      chatBody.appendChild(loadingDiv);
      chatBody.scrollTop = chatBody.scrollHeight;

      try {
          let response = await fetch("/chat", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ message: userInput })
          });

          let data = await response.json();
          
          // Remove loading spinner
          document.getElementById("loading-spinner").remove();
          
          chatBody.innerHTML += `<div><b>Bot:</b> ${data.response}</div>`;
          document.getElementById("chat-input").value = "";
          chatBody.scrollTop = chatBody.scrollHeight;
      } catch (error) {
          // Remove loading spinner and show error message
          document.getElementById("loading-spinner").remove();
          chatBody.innerHTML += `<div class="text-danger"><b>Error:</b> Failed to get response. Please try again.</div>`;
          chatBody.scrollTop = chatBody.scrollHeight;
      }
  }

  // Send button click event
  document.getElementById("send-btn").addEventListener("click", sendMessage);
  
  // Listen for Enter key in the input field
  document.getElementById("chat-input").addEventListener("keypress", function(event) {
      if (event.key === "Enter") {
          event.preventDefault(); // Prevent default form submission
          sendMessage();
      }
  });
});
