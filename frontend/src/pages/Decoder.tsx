import { Link, useSearchParams } from 'react-router-dom'
import { useState, useCallback, useEffect } from 'react'
import {
  decodeBase64,
  encodeBase64,
  decodeUrl,
  encodeUrl,
  decodeHex,
  encodeHex,
  decodeHtmlEntities,
  rot13,
  decodeJwt,
  decompressGzip,
  detectHash,
  verifyHashAgainstCommonWords,
  getHashLookupUrl,
} from '../utils/decoder'

type OpId =
  | 'base64decode'
  | 'base64encode'
  | 'urldecode'
  | 'urlencode'
  | 'hexdecode'
  | 'hexencode'
  | 'htmldecode'
  | 'rot13'
  | 'jwtdecode'
  | 'gzip'

const OPS: { id: OpId; label: string; isAsync?: boolean }[] = [
  { id: 'base64decode', label: 'Base64 Decode' },
  { id: 'base64encode', label: 'Base64 Encode' },
  { id: 'urldecode', label: 'URL Decode' },
  { id: 'urlencode', label: 'URL Encode' },
  { id: 'hexdecode', label: 'Hex Decode' },
  { id: 'hexencode', label: 'Hex Encode' },
  { id: 'htmldecode', label: 'HTML Entities Decode' },
  { id: 'rot13', label: 'ROT13' },
  { id: 'jwtdecode', label: 'JWT Decode' },
  { id: 'gzip', label: 'GZIP Decompress (base64)', isAsync: true },
]

export default function Decoder() {
  const [searchParams] = useSearchParams()
  const initialFromUrl = searchParams.get('input')
  const [input, setInput] = useState('')
  useEffect(() => {
    if (initialFromUrl) {
      try {
        setInput(decodeURIComponent(initialFromUrl))
      } catch {
        setInput(initialFromUrl)
      }
    }
  }, [initialFromUrl])
  const [output, setOutput] = useState('')
  const [error, setError] = useState('')
  const [hashVerifyResult, setHashVerifyResult] = useState('')
  const [hashVerifying, setHashVerifying] = useState(false)

  const runOp = useCallback(async (opId: OpId) => {
    if (!input.trim()) {
      setError('Enter input first')
      setOutput('')
      return
    }
    setError('')
    setOutput('')
    let result: { ok: boolean; output?: string; error?: string }
    switch (opId) {
      case 'base64decode':
        result = decodeBase64(input)
        break
      case 'base64encode':
        result = encodeBase64(input)
        break
      case 'urldecode':
        result = decodeUrl(input)
        break
      case 'urlencode':
        result = encodeUrl(input)
        break
      case 'hexdecode':
        result = decodeHex(input)
        break
      case 'hexencode':
        result = encodeHex(input)
        break
      case 'htmldecode':
        result = decodeHtmlEntities(input)
        break
      case 'rot13':
        result = rot13(input)
        break
      case 'jwtdecode':
        result = decodeJwt(input)
        break
      case 'gzip':
        result = await decompressGzip(input)
        break
      default:
        result = { ok: false, error: 'Unknown op' }
    }
    if (result.ok) setOutput(result.output!)
    else setError(result.error || 'Failed')
  }, [input])

  const runHashVerify = useCallback(async () => {
    if (!input.trim()) return
    setHashVerifying(true)
    setHashVerifyResult('')
    const r = await verifyHashAgainstCommonWords(input)
    setHashVerifyResult(r.ok ? r.output! : r.error)
    setHashVerifying(false)
  }, [input])

  const hashType = detectHash(input.trim())
  const hashLookupUrl = getHashLookupUrl(input.trim())

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <Link to="/report-history" className="neon-btn" style={{ padding: '6px 14px', fontSize: 11, marginBottom: 16, display: 'inline-block' }}>
        &lt; DASHBOARD
      </Link>

      <div className="section-title">[ DECODER ]</div>
      <div className="section-divider">━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</div>
      <p style={{ fontSize: 11, color: 'var(--fg-dim)', marginBottom: 16 }}>
        Paste encoded strings from recon (cookies, tokens, API responses) and try decode/encode operations. Supports Base64, URL, Hex, HTML entities, ROT13, JWT, GZIP.
      </p>

      <div className="panel" style={{ marginBottom: 16 }}>
        <div className="panel-header" style={{ color: 'var(--accent)' }}>INPUT</div>
        <textarea
          className="cyber-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Paste base64, hex, URL-encoded, JWT, or other encoded string..."
          style={{
            width: '100%',
            minHeight: 100,
            fontFamily: 'monospace',
            fontSize: 12,
            padding: 12,
            resize: 'vertical',
          }}
        />
      </div>

      <div className="panel" style={{ marginBottom: 16 }}>
        <div className="panel-header" style={{ color: 'var(--accent)' }}>ENCODE / DECODE</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {OPS.map((op) => (
            <button
              key={op.id}
              type="button"
              className="neon-btn"
              style={{ padding: '6px 12px', fontSize: 11 }}
              onClick={() => runOp(op.id)}
              disabled={op.isAsync && !input.trim()}
            >
              {op.label}
            </button>
          ))}
        </div>
      </div>

      {/* Hash section: detect, verify, lookup */}
      <div className="panel" style={{ marginBottom: 16 }}>
        <div className="panel-header" style={{ color: 'var(--accent)' }}>HASH (MD5 / SHA1 / SHA256)</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
          {hashType && (
            <span style={{ fontSize: 11, color: 'var(--fg-dim)' }}>
              Detected: <strong style={{ color: 'var(--warning)' }}>{hashType.toUpperCase()}</strong>
            </span>
          )}
          <button
            type="button"
            className="neon-btn"
            style={{ padding: '6px 12px', fontSize: 11 }}
            onClick={runHashVerify}
            disabled={hashVerifying || !input.trim()}
          >
            {hashVerifying ? '...' : 'Verify vs common words'}
          </button>
          {hashLookupUrl && (
            <a
              href={hashLookupUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="neon-btn"
              style={{ padding: '6px 12px', fontSize: 11, textDecoration: 'none' }}
            >
              Lookup online
            </a>
          )}
        </div>
        {hashVerifyResult && (
          <div style={{ marginTop: 10, padding: '8px 12px', background: 'rgba(0,0,0,0.3)', fontSize: 12 }}>
            {hashVerifyResult}
          </div>
        )}
      </div>

      {(output || error) && (
        <div className="panel">
          <div className="panel-header" style={{ color: error ? 'var(--error)' : 'var(--accent)' }}>
            {error ? 'ERROR' : 'OUTPUT'}
          </div>
          <pre
            style={{
              margin: 0,
              padding: 12,
              background: '#0d1117',
              overflow: 'auto',
              maxHeight: 300,
              fontSize: 12,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-all',
            }}
          >
            {error || output}
          </pre>
        </div>
      )}
    </div>
  )
}
