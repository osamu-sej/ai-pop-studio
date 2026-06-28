import type { ReactNode } from 'react'

// A small, dependency-free markdown renderer covering the subset Aurora emits:
// headings, bold/italic, inline code, code blocks, lists, blockquotes, links,
// horizontal rules and paragraphs. Keeps the bundle lean and the build offline.

let keySeq = 0
const k = () => `md-${keySeq++}`

type OnCite = (n: number) => void

// Only allow safe link schemes. React does NOT block `javascript:`/`data:` URLs
// in href, so an unsanitised markdown link from an untrusted source could run
// script in the app origin. Anything with another scheme is rendered as text.
function safeHref(url: string): string | null {
  // Browsers strip whitespace — including the tab/newline/CR attackers use for
  // `java\tscript:` — from URLs before parsing, so strip it here too.
  const cleaned = url.replace(/\s+/g, '')
  if (!cleaned) return null
  // Relative links and anchors are always safe.
  if (/^(\/|\.{0,2}\/|#)/.test(cleaned)) return cleaned
  const m = /^([a-zA-Z][a-zA-Z0-9+.-]*):/.exec(cleaned)
  if (!m) return cleaned // no scheme -> treat as a relative path
  const scheme = m[1].toLowerCase()
  return ['http', 'https', 'mailto'].includes(scheme) ? cleaned : null
}

function renderInline(text: string, onCite?: OnCite): ReactNode[] {
  const nodes: ReactNode[] = []
  // Order matters: code first (so ** inside code is literal), then links, bold,
  // italic, and finally bare [n] citation markers.
  const pattern =
    /(`[^`]+`)|(\[[^\]]+\]\([^)]+\))|(\*\*[^*]+\*\*)|(\*[^*]+\*)|(_[^_]+_)|(\[\d+\])/g
  let last = 0
  let m: RegExpExecArray | null
  while ((m = pattern.exec(text)) !== null) {
    if (m.index > last) nodes.push(text.slice(last, m.index))
    const token = m[0]
    if (token.startsWith('`')) {
      nodes.push(<code key={k()} className="md-code">{token.slice(1, -1)}</code>)
    } else if (token.startsWith('[') && token.includes('](')) {
      const lm = /\[([^\]]+)\]\(([^)]+)\)/.exec(token)!
      const href = safeHref(lm[2])
      nodes.push(
        href ? (
          <a key={k()} href={href} target="_blank" rel="noreferrer">
            {lm[1]}
          </a>
        ) : (
          // Unsafe scheme (javascript:, data:, …) -> render as plain text.
          <span key={k()}>{lm[1]}</span>
        ),
      )
    } else if (/^\[\d+\]$/.test(token)) {
      const n = parseInt(token.slice(1, -1), 10)
      nodes.push(
        onCite ? (
          <button key={k()} className="inline-cite" onClick={() => onCite(n)} title={`Source ${n}`}>
            {n}
          </button>
        ) : (
          <sup key={k()} className="inline-cite-static">{n}</sup>
        ),
      )
    } else if (token.startsWith('**')) {
      nodes.push(<strong key={k()}>{token.slice(2, -2)}</strong>)
    } else {
      nodes.push(<em key={k()}>{token.slice(1, -1)}</em>)
    }
    last = m.index + token.length
  }
  if (last < text.length) nodes.push(text.slice(last))
  return nodes
}

export function Markdown({ text, onCite }: { text: string; onCite?: OnCite }) {
  const lines = (text ?? '').replace(/\r\n/g, '\n').split('\n')
  const blocks: ReactNode[] = []
  let i = 0
  let para: string[] = []

  const flushPara = () => {
    if (para.length) {
      blocks.push(<p key={k()}>{renderInline(para.join(' '), onCite)}</p>)
      para = []
    }
  }

  while (i < lines.length) {
    const line = lines[i]

    if (line.trim().startsWith('```')) {
      flushPara()
      const code: string[] = []
      i++
      while (i < lines.length && !lines[i].trim().startsWith('```')) {
        code.push(lines[i])
        i++
      }
      i++ // closing fence
      blocks.push(
        <pre key={k()} className="md-pre">
          <code>{code.join('\n')}</code>
        </pre>,
      )
      continue
    }

    const heading = /^(#{1,6})\s+(.*)$/.exec(line)
    if (heading) {
      flushPara()
      const level = heading[1].length
      const tags = ['h2', 'h3', 'h4', 'h5', 'h6', 'h6'] as const
      const Tag = tags[Math.min(level, 6) - 1]
      blocks.push(
        <Tag key={k()} className="md-h">
          {renderInline(heading[2], onCite)}
        </Tag>,
      )
      i++
      continue
    }

    if (/^\s*([-*=_]){3,}\s*$/.test(line) && line.trim().length >= 3 && !/\w/.test(line)) {
      flushPara()
      blocks.push(<hr key={k()} className="md-hr" />)
      i++
      continue
    }

    if (/^\s*>/.test(line)) {
      flushPara()
      const quote: string[] = []
      while (i < lines.length && /^\s*>/.test(lines[i])) {
        quote.push(lines[i].replace(/^\s*>\s?/, ''))
        i++
      }
      blocks.push(
        <blockquote key={k()} className="md-quote">
          {renderInline(quote.join(' '), onCite)}
        </blockquote>,
      )
      continue
    }

    // unordered list (supports one level of nesting via indentation)
    if (/^\s*[-*]\s+/.test(line)) {
      flushPara()
      const items: ReactNode[] = []
      while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
        const indented = /^\s{2,}[-*]\s+/.test(lines[i])
        const content = lines[i].replace(/^\s*[-*]\s+/, '')
        items.push(
          <li key={k()} className={indented ? 'md-li-nested' : undefined}>
            {renderInline(content, onCite)}
          </li>,
        )
        i++
      }
      blocks.push(<ul key={k()} className="md-ul">{items}</ul>)
      continue
    }

    // ordered list
    if (/^\s*\d+\.\s+/.test(line)) {
      flushPara()
      const items: ReactNode[] = []
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
        items.push(<li key={k()}>{renderInline(lines[i].replace(/^\s*\d+\.\s+/, ''), onCite)}</li>)
        i++
      }
      blocks.push(<ol key={k()} className="md-ol">{items}</ol>)
      continue
    }

    if (line.trim() === '') {
      flushPara()
      i++
      continue
    }

    para.push(line.trim())
    i++
  }
  flushPara()
  return <div className="markdown">{blocks}</div>
}
