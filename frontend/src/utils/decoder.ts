/**
 * Decoder utilities — Base64, URL, Hex, HTML, ROT13, JWT, GZIP
 * Used by Decoder page and inline decode actions.
 */

export type DecodeResult = { ok: true; output: string } | { ok: false; error: string }

export function decodeBase64(input: string): DecodeResult {
  try {
    const s = input.trim().replace(/\s/g, '')
    const decoded = atob(s)
    return { ok: true, output: decoded }
  } catch {
    return { ok: false, error: 'Invalid Base64' }
  }
}

export function encodeBase64(input: string): DecodeResult {
  try {
    return { ok: true, output: btoa(input) }
  } catch {
    return { ok: false, error: 'Encoding failed' }
  }
}

export function decodeUrl(input: string): DecodeResult {
  try {
    return { ok: true, output: decodeURIComponent(input.replace(/\+/g, ' ')) }
  } catch {
    try {
      return { ok: true, output: decodeURI(input) }
    } catch {
      return { ok: false, error: 'Invalid URL encoding' }
    }
  }
}

export function encodeUrl(input: string): DecodeResult {
  try {
    return { ok: true, output: encodeURIComponent(input) }
  } catch {
    return { ok: false, error: 'Encoding failed' }
  }
}

export function decodeHex(input: string): DecodeResult {
  try {
    const hex = input.replace(/\s|0x/gi, '')
    if (!/^[0-9a-f]+$/i.test(hex) || hex.length % 2) {
      return { ok: false, error: 'Invalid hex string' }
    }
    const bytes = new Uint8Array(hex.length / 2)
    for (let i = 0; i < hex.length; i += 2) {
      bytes[i / 2] = parseInt(hex.substr(i, 2), 16)
    }
    const decoder = new TextDecoder('utf-8', { fatal: false })
    return { ok: true, output: decoder.decode(bytes) }
  } catch {
    return { ok: false, error: 'Hex decode failed' }
  }
}

export function encodeHex(input: string): DecodeResult {
  try {
    const encoder = new TextEncoder()
    const bytes = encoder.encode(input)
    const hex = Array.from(bytes).map((b) => b.toString(16).padStart(2, '0')).join('')
    return { ok: true, output: hex }
  } catch {
    return { ok: false, error: 'Encoding failed' }
  }
}

const HTML_ENTITIES: Record<string, string> = {
  '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&apos;': "'",
  '&#39;': "'", '&#x27;': "'", '&#x2F;': '/', '&#60;': '<', '&#62;': '>',
  '&nbsp;': '\u00a0', '&#x3D;': '=', '&#x2F;': '/',
}

export function decodeHtmlEntities(input: string): DecodeResult {
  try {
    let out = input
    for (const [ent, char] of Object.entries(HTML_ENTITIES)) {
      out = out.replace(new RegExp(ent, 'gi'), char)
    }
    out = out.replace(/&#(\d+);/g, (_, n) => String.fromCharCode(parseInt(n, 10)))
    out = out.replace(/&#x([0-9a-f]+);/gi, (_, n) => String.fromCharCode(parseInt(n, 16)))
    return { ok: true, output: out }
  } catch {
    return { ok: false, error: 'HTML decode failed' }
  }
}

export function rot13(input: string): DecodeResult {
  try {
    const out = input.replace(/[a-zA-Z]/g, (c) => {
      const base = c <= 'Z' ? 65 : 97
      return String.fromCharCode(((c.charCodeAt(0) - base + 13) % 26) + base)
    })
    return { ok: true, output: out }
  } catch {
    return { ok: false, error: 'ROT13 failed' }
  }
}

export function decodeJwt(input: string): DecodeResult {
  try {
    const trimmed = input.trim()
    const parts = trimmed.split('.')
    if (parts.length !== 3) return { ok: false, error: 'JWT must have 3 parts (header.payload.signature)' }
    const [headerB64, payloadB64] = parts
    const pad = (s: string) => s + '==='.slice(0, (4 - (s.length % 4)) % 4)
    const b64url = (s: string) => pad(s.replace(/-/g, '+').replace(/_/g, '/'))
    const header = JSON.parse(atob(b64url(headerB64)))
    const payload = JSON.parse(atob(b64url(payloadB64)))
    const pretty = `=== HEADER ===\n${JSON.stringify(header, null, 2)}\n\n=== PAYLOAD ===\n${JSON.stringify(payload, null, 2)}`
    return { ok: true, output: pretty }
  } catch (e) {
    return { ok: false, error: `JWT decode failed: ${e instanceof Error ? e.message : String(e)}` }
  }
}

export async function decompressGzip(base64Input: string): Promise<DecodeResult> {
  try {
    const bin = Uint8Array.from(atob(base64Input.trim().replace(/\s/g, '')), (c) => c.charCodeAt(0))
    const stream = new Blob([bin]).stream().pipeThrough(new DecompressionStream('gzip'))
    const reader = stream.getReader()
    const chunks: Uint8Array[] = []
    // eslint-disable-next-line no-constant-condition
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      if (value) chunks.push(value)
    }
    const len = chunks.reduce((a, c) => a + c.length, 0)
    const result = new Uint8Array(len)
    let off = 0
    for (const c of chunks) {
      result.set(c, off)
      off += c.length
    }
    const text = new TextDecoder('utf-8', { fatal: false }).decode(result)
    return { ok: true, output: text }
  } catch (e) {
    return { ok: false, error: `GZIP decompress failed: ${e instanceof Error ? e.message : String(e)}` }
  }
}

// Hash detection and verification
export type HashType = 'md5' | 'sha1' | 'sha256' | null

export function detectHash(input: string): HashType {
  const s = input.trim()
  if (/^[a-fA-F0-9]{32}$/.test(s)) return 'md5'
  if (/^[a-fA-F0-9]{40}$/.test(s)) return 'sha1'
  if (/^[a-fA-F0-9]{64}$/.test(s)) return 'sha256'
  return null
}

const COMMON_PASSWORDS = [
  'password', '123456', '12345678', 'qwerty', 'abc123', 'monkey', '1234567', 'letmein', 'trustno1',
  'dragon', 'baseball', 'iloveyou', 'master', 'sunshine', 'ashley', 'bailey', 'passw0rd', 'shadow',
  '123123', '654321', 'superman', 'qazwsx', 'michael', 'football', 'admin', 'root', 'toor',
  'password1', 'Password1', 'welcome', 'changeme', 'secret', 'test', 'guest', 'default',
]

function md5Hex(s: string): string {
  function md5cycle(x: number[], k: number[]) {
    let a = x[0], b = x[1], c = x[2], d = x[3]
    a = ff(a, b, c, d, k[0], 7, -680876936)
    d = ff(d, a, b, c, k[1], 12, -389564586)
    c = ff(c, d, a, b, k[2], 17, 606105819)
    b = ff(b, c, d, a, k[3], 22, -1044525330)
    a = ff(a, b, c, d, k[4], 7, -176418897)
    d = ff(d, a, b, c, k[5], 12, 1200080426)
    c = ff(c, d, a, b, k[6], 17, -1473231341)
    b = ff(b, c, d, a, k[7], 22, -45705983)
    a = ff(a, b, c, d, k[8], 7, 1770035416)
    d = ff(d, a, b, c, k[9], 12, -1958414417)
    c = ff(c, d, a, b, k[10], 17, -42063)
    b = ff(b, c, d, a, k[11], 22, -1990404162)
    a = ff(a, b, c, d, k[12], 7, 1804603682)
    d = ff(d, a, b, c, k[13], 12, -40341101)
    c = ff(c, d, a, b, k[14], 17, -1502002290)
    b = ff(b, c, d, a, k[15], 22, 1236535329)
    a = gg(a, b, c, d, k[1], 5, -165796510)
    d = gg(d, a, b, c, k[6], 9, -1069501632)
    c = gg(c, d, a, b, k[11], 14, 643717713)
    b = gg(b, c, d, a, k[0], 20, -373897302)
    a = gg(a, b, c, d, k[5], 5, -701558691)
    d = gg(d, a, b, c, k[10], 9, 38016083)
    c = gg(c, d, a, b, k[15], 14, -660478335)
    b = gg(b, c, d, a, k[4], 20, -405537848)
    a = gg(a, b, c, d, k[9], 5, 568446438)
    d = gg(d, a, b, c, k[14], 9, -1019803690)
    c = gg(c, d, a, b, k[3], 14, -187363961)
    b = gg(b, c, d, a, k[8], 20, 1163531501)
    a = gg(a, b, c, d, k[13], 5, -1444681467)
    d = gg(d, a, b, c, k[2], 9, -51403784)
    c = gg(c, d, a, b, k[7], 14, 1735328473)
    b = gg(b, c, d, a, k[12], 20, -1926607734)
    a = hh(a, b, c, d, k[5], 4, -378558)
    d = hh(d, a, b, c, k[8], 11, -2022574463)
    c = hh(c, d, a, b, k[11], 16, 1839030562)
    b = hh(b, c, d, a, k[14], 23, -35309556)
    a = hh(a, b, c, d, k[1], 4, -1530992060)
    d = hh(d, a, b, c, k[4], 11, 1272893353)
    c = hh(c, d, a, b, k[7], 16, -155497632)
    b = hh(b, c, d, a, k[10], 23, -1094730640)
    a = hh(a, b, c, d, k[13], 4, 681279174)
    d = hh(d, a, b, c, k[0], 11, -358537222)
    c = hh(c, d, a, b, k[3], 16, -722521979)
    b = hh(b, c, d, a, k[6], 23, 76029189)
    a = hh(a, b, c, d, k[9], 4, -640364487)
    d = hh(d, a, b, c, k[12], 11, -421815835)
    c = hh(c, d, a, b, k[15], 16, 530742520)
    b = hh(b, c, d, a, k[2], 23, -995338651)
    a = ii(a, b, c, d, k[0], 6, -198630844)
    d = ii(d, a, b, c, k[7], 10, 1126891415)
    c = ii(c, d, a, b, k[14], 15, -1416354905)
    b = ii(b, c, d, a, k[5], 21, -57434055)
    a = ii(a, b, c, d, k[12], 6, 1700485571)
    d = ii(d, a, b, c, k[3], 10, -1894986606)
    c = ii(c, d, a, b, k[10], 15, -1051523)
    b = ii(b, c, d, a, k[1], 21, -2054922799)
    a = ii(a, b, c, d, k[8], 6, 1873313359)
    d = ii(d, a, b, c, k[15], 10, -30611744)
    c = ii(c, d, a, b, k[6], 15, -1560198380)
    b = ii(b, c, d, a, k[13], 21, 1309151649)
    a = ii(a, b, c, d, k[4], 6, -145523070)
    d = ii(d, a, b, c, k[11], 10, -1120210379)
    c = ii(c, d, a, b, k[2], 15, 718787259)
    b = ii(b, c, d, a, k[9], 21, -343485551)
    x[0] = add32(a, x[0]); x[1] = add32(b, x[1]); x[2] = add32(c, x[2]); x[3] = add32(d, x[3])
  }
  function cmn(q: number, a: number, b: number, x: number, s: number, t: number) {
    a = add32(add32(a, q), add32(x, t))
    return add32((a << s) | (a >>> (32 - s)), b)
  }
  function ff(a: number, b: number, c: number, d: number, x: number, s: number, t: number) {
    return cmn((b & c) | (~b & d), a, b, x, s, t)
  }
  function gg(a: number, b: number, c: number, d: number, x: number, s: number, t: number) {
    return cmn((b & d) | (c & ~d), a, b, x, s, t)
  }
  function hh(a: number, b: number, c: number, d: number, x: number, s: number, t: number) {
    return cmn(b ^ c ^ d, a, b, x, s, t)
  }
  function ii(a: number, b: number, c: number, d: number, x: number, s: number, t: number) {
    return cmn(c ^ (b | ~d), a, b, x, s, t)
  }
  function md51(s: string) {
    const n = s.length; const state = [1732584193, -271733879, -1732584194, 271733878]
    let i: number
    for (i = 64; i <= s.length; i += 64) {
      md5cycle(state, md5blk(s.substring(i - 64, i)))
    }
    s = s.substring(i - 64)
    const tail = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    for (i = 0; i < s.length; i++) tail[i >> 2] |= s.charCodeAt(i) << (i % 4 * 8)
    tail[i >> 2] |= 0x80 << (i % 4 * 8)
    if (i > 55) {
      md5cycle(state, tail)
      for (i = 0; i < 16; i++) tail[i] = 0
    }
    tail[14] = n * 8
    md5cycle(state, tail)
    return state
  }
  function md5blk(s: string) {
    const md5blks: number[] = []
    for (let i = 0; i < 64; i += 4) {
      md5blks[i >> 2] = s.charCodeAt(i) + (s.charCodeAt(i + 1) << 8) + (s.charCodeAt(i + 2) << 16) + (s.charCodeAt(i + 3) << 24)
    }
    return md5blks
  }
  const hex_chr = '0123456789abcdef'.split('')
  function rhex(n: number) {
    let s = ''
    for (let j = 0; j < 4; j++) s += hex_chr[(n >> (j * 8 + 4)) & 0x0F] + hex_chr[(n >> (j * 8)) & 0x0F]
    return s
  }
  function add32(a: number, b: number) {
    return (a + b) & 0xFFFFFFFF
  }
  return md51(s).map(rhex).join('')
}

async function hashString(algo: 'MD5' | 'SHA-1' | 'SHA-256', text: string): Promise<string> {
  if (algo === 'MD5') return md5Hex(text)
  const buf = new TextEncoder().encode(text)
  const hash = await crypto.subtle.digest(algo, buf)
  return Array.from(new Uint8Array(hash)).map((b) => b.toString(16).padStart(2, '0')).join('')
}

export async function verifyHashAgainstCommonWords(hashInput: string): Promise<DecodeResult> {
  const type = detectHash(hashInput)
  if (!type) return { ok: false, error: 'Not a recognized hash (MD5=32, SHA1=40, SHA256=64 hex chars)' }
  const algo = type === 'md5' ? 'MD5' : type === 'sha1' ? 'SHA-1' : 'SHA-256'
  const target = hashInput.toLowerCase()
  for (const pwd of COMMON_PASSWORDS) {
    const h = await hashString(algo, pwd)
    if (h === target) return { ok: true, output: `Match: "${pwd}" (${type.toUpperCase()})` }
  }
  return { ok: true, output: `No match in ${COMMON_PASSWORDS.length} common passwords (${type.toUpperCase()})` }
}

/** Detect if a string looks encoded (base64, hex, JWT, URL-encoded) */
export function looksEncoded(s: string): boolean {
  const t = s.trim()
  if (!t || t.length < 8) return false
  if (t.split('.').length === 3 && /^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(t)) return true // JWT
  if (/^[A-Za-z0-9+/]+=*$/.test(t) && t.length % 4 === 0) return true // base64
  if (/^[0-9a-fA-F]+$/.test(t) && (t.length === 32 || t.length === 40 || t.length === 64)) return true // hash
  if (/^[0-9a-fA-F\s]+$/.test(t) && t.replace(/\s/g, '').length >= 16) return true // hex
  if (/%[0-9a-fA-F]{2}/.test(t)) return true // URL encoded
  return false
}

export const HASH_LOOKUP_URLS: Record<string, string> = {
  md5: 'https://hashes.com/en/decrypt/hash',
  sha1: 'https://hashes.com/en/decrypt/hash',
  sha256: 'https://hashes.com/en/decrypt/hash',
}

export function getHashLookupUrl(hash: string): string {
  const type = detectHash(hash)
  if (!type) return ''
  return `${HASH_LOOKUP_URLS[type]}?hash=${encodeURIComponent(hash)}`
}
