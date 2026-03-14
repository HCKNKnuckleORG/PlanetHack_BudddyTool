import { Link } from 'react-router-dom'

const ASCII_BANNER = `
  ██████╗ ██╗      █████╗ ███╗   ██╗███████╗████████╗
  ██╔══██╗██║     ██╔══██╗████╗  ██║██╔════╝╚══██╔══╝
  ██████╔╝██║     ███████║██╔██╗ ██║█████╗     ██║   
  ██╔═══╝ ██║     ██╔══██║██║╚██╗██║██╔══╝     ██║   
  ██║     ███████╗██║  ██║██║ ╚████║███████╗   ██║   
  ╚═╝     ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   

  ██╗  ██╗ █████╗  ██████╗██╗  ██╗
  ██║  ██║██╔══██╗██╔════╝██║ ██╔╝
  ███████║███████║██║     █████╔╝ 
  ██╔══██║██╔══██║██║     ██╔═██╗ 
  ██║  ██║██║  ██║╚██████╗██║  ██╗
  ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
`

export default function Home() {
  return (
    <div className="home-container">
      <pre className="ascii-banner">{ASCII_BANNER}</pre>
      <div className="tagline">//  CTF & BUG BOUNTY TOOLKIT  //</div>
      <div className="section-divider">━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</div>
      <div className="home-prompt">WHAT DO YOU WANT TO DO?</div>

      <div className="btn-grid home-three-col" style={{ marginBottom: 16 }}>
        <Link to="/modules" className="neon-btn green" style={{ minWidth: 220 }}>
          MODULES (RECON, BRUTE FORCE, XSS, etc.)
        </Link>
        <Link to="/report-history" className="neon-btn cyan" style={{ minWidth: 220 }}>
          DASHBOARD (RESULTS + NEXT STEPS)
        </Link>
        <Link to="/terminal" className="neon-btn yellow" style={{ minWidth: 220 }}>
          TERMINAL (LIVE OUTPUT)
        </Link>
      </div>
    </div>
  )
}
