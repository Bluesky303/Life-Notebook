function escapeHtml(input: string): string {
  return input
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function inlineMarkdown(input: string): string {
  let s = escapeHtml(input);
  s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
  s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  s = s.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>');
  s = s.replace(/\$([^$]+)\$/g, '<span class="md-math">$1</span>');
  return s;
}

export function markdownToHtml(markdown: string): string {
  const lines = markdown.replaceAll("\r\n", "\n").split("\n");
  const html: string[] = [];
  let inCode = false;
  let inList = false;

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();

    if (line.startsWith("```")) {
      if (!inCode) {
        if (inList) {
          html.push("</ul>");
          inList = false;
        }
        inCode = true;
        html.push("<pre><code>");
      } else {
        inCode = false;
        html.push("</code></pre>");
      }
      continue;
    }

    if (inCode) {
      html.push(`${escapeHtml(rawLine)}\n`);
      continue;
    }

    if (line.startsWith("- ")) {
      if (!inList) {
        html.push("<ul>");
        inList = true;
      }
      html.push(`<li>${inlineMarkdown(line.slice(2))}</li>`);
      continue;
    }

    if (inList) {
      html.push("</ul>");
      inList = false;
    }

    if (!line) {
      continue;
    }

    const h6 = line.match(/^######\s+(.*)$/);
    const h5 = line.match(/^#####\s+(.*)$/);
    const h4 = line.match(/^####\s+(.*)$/);
    const h3 = line.match(/^###\s+(.*)$/);
    const h2 = line.match(/^##\s+(.*)$/);
    const h1 = line.match(/^#\s+(.*)$/);

    if (h1) html.push(`<h1>${inlineMarkdown(h1[1])}</h1>`);
    else if (h2) html.push(`<h2>${inlineMarkdown(h2[1])}</h2>`);
    else if (h3) html.push(`<h3>${inlineMarkdown(h3[1])}</h3>`);
    else if (h4) html.push(`<h4>${inlineMarkdown(h4[1])}</h4>`);
    else if (h5) html.push(`<h5>${inlineMarkdown(h5[1])}</h5>`);
    else if (h6) html.push(`<h6>${inlineMarkdown(h6[1])}</h6>`);
    else if (line.startsWith("> ")) html.push(`<blockquote>${inlineMarkdown(line.slice(2))}</blockquote>`);
    else html.push(`<p>${inlineMarkdown(line)}</p>`);
  }

  if (inList) {
    html.push("</ul>");
  }
  if (inCode) {
    html.push("</code></pre>");
  }

  return html.join("\n");
}
