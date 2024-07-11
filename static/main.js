const chatbotToggler = document.querySelector(".chatbot-toggler");
const closeBtn = document.querySelector(".close-btn");
const chatbox = document.querySelector(".chatbox");
const chatInput = document.querySelector(".chat-input textarea");
const sendChatBtn = document.querySelector(".chat-input span");
const initMessage = document.querySelector(".init-message");

let userMessage = null;
const inputInitHeight = chatInput.scrollHeight;

const createChatLi = (message, className) => {
  const chatLi = document.createElement("li");
  chatLi.classList.add("chat", `${className}`);
  let chatContent =
    className === "outgoing"
      ? `<p></p>`
      : `<span class="material-symbols-outlined">smart_toy</span><p></p>`;
  chatLi.innerHTML = chatContent;
  chatLi.querySelector("p").textContent = message;
  return chatLi;
};

const generateResponse = (message) => {
  const API_URL = "http://localhost:8000/process";
  const requestBody = {
    session_id: sessionStorage.getItem("session_id"),
    message: message
  };

  const requestOptions = {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(requestBody)
  };

  const thinkingMessage = createChatLi("Thinking...", "incoming");
  chatbox.appendChild(thinkingMessage);
  chatbox.scrollTo(0, chatbox.scrollHeight);

  fetch(API_URL, requestOptions)
    .then((res) => res.json())
    .then((data) => {
      chatbox.removeChild(thinkingMessage);

      const responseLi = createChatLi(data.response, "incoming");
      chatbox.appendChild(responseLi);
      chatbox.scrollTo(0, chatbox.scrollHeight);
    })
    .catch((error) => {
      console.error("Error calling Process API:", error);
    });
};

const callInitAPI = () => {
  const API_URL = "http://localhost:8000/init";

  fetch(API_URL)
    .then((res) => res.json())
    .then((data) => {
      sessionStorage.setItem("session_id", data.session_id);
      initMessage.textContent = data.response;
    })
    .catch((error) => {
      console.error("Error calling Init API:", error);
    });
};

const handleChat = () => {
  userMessage = chatInput.value.trim();
  if (!userMessage) return;

  chatInput.value = "";
  chatInput.style.height = `${inputInitHeight}px`;

  chatbox.appendChild(createChatLi(userMessage, "outgoing"));
  chatbox.scrollTo(0, chatbox.scrollHeight);

  setTimeout(() => {
    generateResponse(userMessage);
  }, 600);
};

chatInput.addEventListener("input", () => {
  chatInput.style.height = `${inputInitHeight}px`;
  chatInput.style.height = `${chatInput.scrollHeight}px`;
});

chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && window.innerWidth > 800) {
    e.preventDefault();
    handleChat();
  }
});

sendChatBtn.addEventListener("click", handleChat);
closeBtn.addEventListener("click", () =>
  document.body.classList.remove("show-chatbot")
);

chatbotToggler.addEventListener("click", () => {
  document.body.classList.toggle("show-chatbot");

  if (!sessionStorage.getItem("session_id")) {
    callInitAPI();
  }
});

window.onload = function() {
  sessionStorage.clear();
};
window.addEventListener("beforeunload", function(event) {
  const sessionID = sessionStorage.getItem("session_id");
  if (sessionID) {
    const API_URL = `http://localhost:8000/removesession/${sessionID}`;

    fetch(API_URL, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json"
      }
    })
    .then((res) => {
    })
    .catch((error) => {
    });
  }
});