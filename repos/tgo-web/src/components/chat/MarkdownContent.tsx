import React, { useMemo } from 'react';
import { Marked, RendererObject, RendererThis, Tokens } from 'marked';
import { markedHighlight } from "marked-highlight";
import hljs from 'highlight.js';
import DOMPurify from 'dompurify';

interface MarkdownContentProps {
  content: string;
  className?: string;
}

const headingClassMap: Record<number, string> = {
  1: 'text-2xl font-bold mb-4 mt-6 text-gray-900 border-b pb-2',
  2: 'text-xl font-bold mb-3 mt-5 text-gray-900 border-b pb-2',
  3: 'text-lg font-bold mb-2 mt-4 text-gray-900',
  4: 'text-base font-bold mb-2 mt-3 text-gray-900',
  5: 'text-sm font-bold mb-2 mt-3 text-gray-900',
  6: 'text-xs font-bold mb-2 mt-3 text-gray-700'
};

const escapeHtml = (value: string): string =>
  value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');

const sanitizeHref = (href?: string | null): string => {
  if (!href) return '';
  const trimmed = href.trim();

  if (trimmed.startsWith('#')) {
    return trimmed;
  }

  try {
    const url = new URL(trimmed, 'http://localhost');
    if (['http:', 'https:', 'mailto:', 'tel:'].includes(url.protocol)) {
      return trimmed;
    }
  } catch {
    if (trimmed.startsWith('mailto:') || trimmed.startsWith('tel:') || trimmed.startsWith('/')) {
      return trimmed;
    }
  }

  return '#';
};

const renderer: RendererObject = {
  heading(this: RendererThis, { tokens, depth }: Tokens.Heading) {
    const html = this.parser.parseInline(tokens);
    const clz = headingClassMap[depth] || 'font-bold mt-4 mb-2 text-gray-900';
    return `<h${depth} class="${clz}">${html}</h${depth}>`;
  },
  // paragraph(this: RendererThis, { tokens }: Tokens.Paragraph) {
  //   const html = this.parser.parseInline(tokens);
  //   return `<p class="mb-3 leading-relaxed text-gray-800">${html}</p>`;
  // },
  link(this: RendererThis, { href, title, tokens }: Tokens.Link) {
    const html = this.parser.parseInline(tokens);
    const safeHref = sanitizeHref(href);
    const titleAttr = title ? ` title="${escapeHtml(title)}"` : '';
    return `<a href="${escapeHtml(safeHref)}"${titleAttr} target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline break-words">${html}</a>`;
  },
  list(this: RendererThis, token: Tokens.List) {
    const itemsHtml = token.items
      .map(item => {
        const rawContent = this.parser.parse(item.tokens);
        const trimmed = rawContent.trim();
        const singleParagraphMatch = trimmed.match(/^<p>([\s\S]*)<\/p>$/);
        const content = singleParagraphMatch ? singleParagraphMatch[1].trim() : trimmed;

        const checkbox = item.task
          ? `<input type="checkbox" class="mr-2 h-3.5 w-3.5 align-middle rounded border border-gray-300 text-blue-500" disabled ${item.checked ? 'checked' : ''} />`
          : '';

        return `<li class="text-gray-800 leading-relaxed">${checkbox}${content}</li>`;
      })
      .join('');
    const startAttr = token.ordered && token.start && token.start !== 1 ? ` start="${token.start}"` : '';
    if (token.ordered) {
      return `<ol${startAttr} class="list-decimal mb-3 space-y-1 ml-6">${itemsHtml}</ol>`;
    }
    return `<ul class="list-disc mb-3 space-y-1 ml-6">${itemsHtml}</ul>`;
  },
  blockquote(this: RendererThis, { tokens }: Tokens.Blockquote) {
    const html = this.parser.parse(tokens);
    return `<blockquote class="border-l-4 border-gray-300 pl-4 py-2 my-3 italic text-gray-700 bg-gray-50">${html}</blockquote>`;
  },
  hr() {
    return '<hr class="my-4 border-t border-gray-300" />';
  },
  table(this: RendererThis, token: Tokens.Table) {
    const headerRow = token.header
      .map((cell, index) => {
        const align = token.align[index];
        const alignAttr = align ? ` style="text-align:${align}"` : '';
        const content = this.parser.parseInline(cell.tokens);
        return `<th class="px-4 py-2 text-left text-sm font-semibold text-gray-900 border border-gray-300"${alignAttr}>${content}</th>`;
      })
      .join('');

    const headerSection = headerRow
      ? `<thead class="bg-gray-100"><tr class="border-b border-gray-300">${headerRow}</tr></thead>`
      : '';

    const bodyRows = token.rows
      .map(row => {
        const cells = row
          .map((cell, index) => {
            const align = token.align[index];
            const alignAttr = align ? ` style="text-align:${align}"` : '';
            const content = this.parser.parseInline(cell.tokens);
            return `<td class="px-4 py-2 text-sm text-gray-800 border border-gray-300"${alignAttr}>${content}</td>`;
          })
          .join('');
        return `<tr class="border-b border-gray-300">${cells}</tr>`;
      })
      .join('');

    return `
      <div class="my-3 overflow-x-auto">
        <table class="min-w-full border-collapse border border-gray-300">
          ${headerSection}
          <tbody>${bodyRows}</tbody>
        </table>
      </div>
    `;
  },
  strong(this: RendererThis, { tokens }: Tokens.Strong) {
    const html = this.parser.parseInline(tokens);
    return `<strong class="font-bold text-gray-900">${html}</strong>`;
  },
  em(this: RendererThis, { tokens }: Tokens.Em) {
    const html = this.parser.parseInline(tokens);
    return `<em class="italic text-gray-800">${html}</em>`;
  },
  del(this: RendererThis, { tokens }: Tokens.Del) {
    const html = this.parser.parseInline(tokens);
    return `<del class="line-through text-gray-600">${html}</del>`;
  },
  image(this: RendererThis, { href, title, text }: Tokens.Image) {
    const safeSrc = sanitizeHref(href);
    const titleAttr = title ? ` title="${escapeHtml(title)}"` : '';
    return `<img src="${escapeHtml(safeSrc)}" alt="${escapeHtml(text || '')}"${titleAttr} class="max-w-full h-auto rounded-lg my-3" loading="lazy" />`;
  }
};

// marked.use({gfm: true, breaks: false });

const marked = new Marked(markedHighlight({
  emptyLangClass: 'hljs',
  langPrefix: 'hljs language-',
  highlight(code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext';
    return hljs.highlight(code, { language }).value;
  }
}));

marked.use({
    renderer,
    gfm: true,
});


const MARKDOWN_CACHE_LIMIT = 200;
const markdownCache = new Map<string, string>();

const renderMarkdownToHtml = (markdown: string): string => {
  if (!markdown) return '';

  const cached = markdownCache.get(markdown);
  if (cached) {
    return cached;
  }

  const parsed = marked.parse(markdown) as string;
  const sanitized = typeof window !== 'undefined'
    ? DOMPurify.sanitize(parsed, { USE_PROFILES: { html: true } })
    : parsed;

  markdownCache.set(markdown, sanitized);
  if (markdownCache.size > MARKDOWN_CACHE_LIMIT) {
    const firstKey = markdownCache.keys().next().value;
    if (firstKey) {
      markdownCache.delete(firstKey);
    }
  }

  return sanitized;
};

/**
 * Markdown Content Renderer Component
 * Renders markdown content using Marked with caching and sanitization for performance & safety
 */
const MarkdownContent: React.FC<MarkdownContentProps> = ({ content, className = '' }) => {
  const html = useMemo(() => renderMarkdownToHtml(content || ''), [content]);
  const combinedClassName = className
    ? `markdown-content ${className}`.trim()
    : 'markdown-content';

  return (
    <div
      className={combinedClassName}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};

export default MarkdownContent;
