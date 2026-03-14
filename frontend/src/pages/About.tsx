import { Link } from 'react-router-dom'

export default function About() {
  return (
    <div style={{ maxWidth: 720, margin: '0 auto' }}>
      <Link to="/report-history" className="neon-btn" style={{ padding: '6px 14px', fontSize: 11, marginBottom: 16, display: 'inline-block' }}>
        &lt; DASHBOARD
      </Link>

      <div className="section-title">[ ABOUT ]</div>
      <div className="section-divider">━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</div>

      <div className="panel" style={{ marginBottom: 20 }}>
        <div className="panel-header" style={{ color: 'var(--accent)' }}>PLANETHACK</div>
        <p style={{ fontSize: 12, color: 'var(--fg)', lineHeight: 1.6 }}>
          CTF and bug bounty reconnaissance workflow for lab environments—Hack The Box, TryHackMe, PwnLab, VulnHub—and authorized testing. Run recon, view findings, get next-step recommendations, and use the Decoder for encoded data.
        </p>
        <p style={{ fontSize: 11, color: 'var(--fg-dim)', marginTop: 12 }}>
          by HCKNKnuckle
        </p>
      </div>

      <div className="panel" style={{ marginBottom: 20 }}>
        <div className="panel-header" style={{ color: 'var(--accent)' }}>CREDITS & THANKS</div>
        <p style={{ fontSize: 11, color: 'var(--fg-dim)', marginBottom: 16 }}>
          PlanetHack integrates and uses the following projects. We extend our thanks to their creators and communities.
        </p>

        <div style={{ marginBottom: 20 }}>
          <div style={{ fontWeight: 'bold', color: 'var(--fg)', marginBottom: 4 }}>Payloads All The Things</div>
          <p style={{ fontSize: 11, color: 'var(--fg-dim)', margin: '0 0 8px 0', lineHeight: 1.5 }}>
            Curated list of payloads and bypasses for web application security testing. Used across modules for SQLi, XSS, LFI, and other attack techniques.
          </p>
          <a
            href="https://github.com/swisskyrepo/PayloadsAllTheThings"
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: 'var(--accent)', fontSize: 11, textDecoration: 'underline' }}
          >
            github.com/swisskyrepo/PayloadsAllTheThings
          </a>
          <p style={{ fontSize: 10, color: 'var(--fg-dim)', marginTop: 4 }}>
            Thanks to <strong>Swissky</strong> and contributors for maintaining this invaluable resource.
          </p>
        </div>

        <div>
          <div style={{ fontWeight: 'bold', color: 'var(--fg)', marginBottom: 4 }}>OWASP Top 10</div>
          <p style={{ fontSize: 11, color: 'var(--fg-dim)', margin: '0 0 8px 0', lineHeight: 1.5 }}>
            Module categories align with OWASP Top 10 2025 for application security testing.
          </p>
          <a
            href="https://owasp.org/Top10/2025/"
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: 'var(--accent)', fontSize: 11, textDecoration: 'underline' }}
          >
            owasp.org/Top10/2025
          </a>
        </div>

        <div style={{ marginTop: 20 }}>
          <div style={{ fontWeight: 'bold', color: 'var(--fg)', marginBottom: 4 }}>Ollama</div>
          <p style={{ fontSize: 11, color: 'var(--fg-dim)', margin: '0 0 8px 0', lineHeight: 1.5 }}>
            Local LLM inference. Used in select modules for AI-assisted next-step suggestions, report summarization, and analysis.
          </p>
          <a
            href="https://ollama.ai"
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: 'var(--accent)', fontSize: 11, textDecoration: 'underline', marginRight: 12 }}
          >
            ollama.ai
          </a>
          <a
            href="https://github.com/ollama/ollama"
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: 'var(--accent)', fontSize: 11, textDecoration: 'underline' }}
          >
            github.com/ollama/ollama
          </a>
          <p style={{ fontSize: 10, color: 'var(--fg-dim)', marginTop: 4 }}>
            Thanks to the Ollama team for making local LLM inference simple and accessible.
          </p>
        </div>
      </div>
    </div>
  )
}
