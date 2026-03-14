/* Digital rain animation -- HTML5 Canvas (legacy Jinja2) */
(function (): void {
  const canvas = document.getElementById("matrix-canvas") as HTMLCanvasElement | null;
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const CHARS =
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*<>{}[]|/\\~^" +
    "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン";

  const FONT_SIZE = 14;
  const FRAME_INTERVAL = 80; /* ms between updates -- lower = faster */
  let columns: number[] = [];
  let w = 0;
  let h = 0;
  let colCount = 0;
  let lastTime = 0;

  function resize(): void {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
    colCount = Math.floor(w / FONT_SIZE);
    columns = [];
    for (let i = 0; i < colCount; i++) {
      columns.push(Math.random() * -100);
    }
  }

  function draw(timestamp: number): void {
    requestAnimationFrame(draw);

    if (timestamp - lastTime < FRAME_INTERVAL) return;
    lastTime = timestamp;

    ctx.fillStyle = "rgba(10, 10, 10, 0.06)";
    ctx.fillRect(0, 0, w, h);

    for (let i = 0; i < colCount; i++) {
      const ch = CHARS[Math.floor(Math.random() * CHARS.length)];
      const x = i * FONT_SIZE;
      const y = columns[i] * FONT_SIZE;

      ctx.fillStyle = "#ffffff";
      ctx.font = FONT_SIZE + "px 'Courier New', monospace";
      ctx.fillText(ch, x, y);

      ctx.fillStyle = "#00ff41";
      ctx.fillText(ch, x, y - FONT_SIZE);

      columns[i]++;
      if (y > h && Math.random() > 0.975) {
        columns[i] = 0;
      }
    }
  }

  window.addEventListener("resize", resize);
  resize();
  requestAnimationFrame(draw);
})();
