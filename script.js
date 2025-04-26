import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
mermaid.initialize({ startOnLoad: true, theme: "dark" });

let lastContent = "";

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
      }
    }
  } catch (error) {
    console.error("Error fetching content:", error);
  }
}

setInterval(fetchContent, 100); // fetch every 100ms for quick updates without needing to refresh page
