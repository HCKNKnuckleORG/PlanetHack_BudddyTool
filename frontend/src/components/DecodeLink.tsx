import { useNavigate } from 'react-router-dom'
import { looksEncoded } from '../utils/decoder'

/**
 * Renders text with a "Try decode" link when it looks encoded (base64, hex, JWT, etc.)
 */
export default function DecodeLink({ text, maxLen = 120 }: { text: string; maxLen?: number }) {
  const navigate = useNavigate()
  const trimmed = String(text || '').trim()
  const display = trimmed.length > maxLen ? trimmed.slice(0, maxLen) + '…' : trimmed
  const showDecode = looksEncoded(trimmed)

  if (!trimmed) return null

  return (
    <span>
      <span style={{ wordBreak: 'break-all' }}>{display}</span>
      {showDecode && (
        <button
          type="button"
          onClick={() => navigate(`/decoder?input=${encodeURIComponent(trimmed)}`)}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--accent)',
            cursor: 'pointer',
            fontSize: 10,
            marginLeft: 6,
            textDecoration: 'underline',
          }}
        >
          Try decode
        </button>
      )}
    </span>
  )
}
