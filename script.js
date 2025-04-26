import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";

mermaid.initialize({ startOnLoad: true, theme: "dark" });

let lastContent = "";
let lastTranscriptId = 0;

async function fetchContent() {
  try {
    const response = await fetch("content.html");

    if (response.ok) {
      const text = await response.text();

      // only update if content is new
      if (text !== lastContent) {
        // wait until the new content is fully fetched and ready
        lastContent = text; // update stored content

        const contentElement = document.getElementById("content");
        contentElement.innerHTML = text; // replace content
        mermaid.run(); // re-render mermaid diagrams
        window.MathJax.typeset();
        MathJax.typeset();
      }
    }
  } catch (error) {
    console.error("Error fetching content:", error);
  }
}

async function fetchTranscript() {
  try {
    const response = await fetch("transcript.json");

    if (response.ok) {
      const data = await response.json();

      // only show toast if transcript ID is new
      if (data.id > lastTranscriptId && data.text) {
        lastTranscriptId = data.id;

        Toastify({
          text: data.text,
          duration: 5000,
          gravity: "bottom",
          position: "center",
          style: {
            background: "rgba(0, 0, 0, 0.5)",
            boxShadow: "0 0 20px rgba(0, 0, 0, 0.33)",
            borderRadius: "8px",
            color: "#fffd",
            fontFamily: "Inter, sans-serif",
            padding: "16px",
          },
        }).showToast();
      }
    }
  } catch (error) {
    console.error("Error fetching transcript:", error);
  }
}

const themeToggle = document.getElementById("theme-toggle");
const body = document.body;

// themeToggle.addEventListener("click", () => {
//   body.classList.toggle("dark");
// });

setInterval(fetchContent, 100); // fetch every 100ms for quick updates without needing to refresh page
setInterval(fetchTranscript, 100); // fetch transcript every 100ms
