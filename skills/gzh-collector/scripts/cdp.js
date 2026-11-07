// Minimal CDP client for controlling the headed Chromium on :1 (port 9222)
// Usage:
//   node cdp.js nav <url>            -> navigate current tab
//   node cdp.js screenshot <out.png> -> capture viewport
//   node cdp.js eval '<js>'          -> evaluate async JS in page, print JSON result
//   node cdp.js info                 -> current tab url/title
const PORT = 9222;

async function target() {
  const list = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
  const page = list.find(t => t.type === 'page');
  if (!page) throw new Error('no page target');
  return page;
}

function cdp(wsUrl) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    let id = 0;
    const pending = new Map();
    ws.onopen = () => resolve({
      send(method, params = {}) {
        return new Promise((res, rej) => {
          const mid = ++id;
          pending.set(mid, { res, rej });
          ws.send(JSON.stringify({ id: mid, method, params }));
        });
      },
      close() { ws.close(); },
    });
    ws.onerror = (e) => reject(new Error('ws error'));
    ws.onmessage = (ev) => {
      const m = JSON.parse(ev.data);
      if (m.id && pending.has(m.id)) {
        const { res, rej } = pending.get(m.id);
        pending.delete(m.id);
        m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result);
      }
    };
  });
}

const [,, cmd, ...args] = process.argv;
const page = await target();
const c = await cdp(page.webSocketDebuggerUrl);

try {
  if (cmd === 'nav') {
    await c.send('Page.navigate', { url: args[0] });
    await new Promise(r => setTimeout(r, 4000));
    const { result: { value } } = await c.send('Runtime.evaluate', { expression: 'JSON.stringify({u:location.href,t:document.title})', returnByValue: true });
    console.log(value);
  } else if (cmd === 'screenshot') {
    const { data } = await c.send('Page.captureScreenshot', { format: 'png' });
    const { writeFileSync } = await import('node:fs');
    writeFileSync(args[0], Buffer.from(data, 'base64'));
    const { result: { value } } = await c.send('Runtime.evaluate', { expression: 'JSON.stringify({u:location.href,t:document.title})', returnByValue: true });
    console.log('saved', args[0], value);
  } else if (cmd === 'shotclip') {
    // node cdp.js shotclip out.png x y w h scale
    const [x, y, w2, h2, sc] = args.slice(1).map(Number);
    const { data } = await c.send('Page.captureScreenshot', { format: 'png', clip: { x, y, width: w2, height: h2, scale: sc || 4 } });
    const { writeFileSync } = await import('node:fs');
    writeFileSync(args[0], Buffer.from(data, 'base64'));
    console.log('saved', args[0]);
  } else if (cmd === 'eval') {
    const { result, exceptionDetails } = await c.send('Runtime.evaluate', {
      expression: `(async () => { ${args[0]} })()`,
      returnByValue: true, awaitPromise: true,
    });
    if (exceptionDetails) console.log('ERR', JSON.stringify(exceptionDetails).slice(0, 1500));
    else console.log(typeof result.value === 'string' ? result.value : JSON.stringify(result.value));
  } else if (cmd === 'info') {
    const { result: { value } } = await c.send('Runtime.evaluate', { expression: 'JSON.stringify({u:location.href,t:document.title})', returnByValue: true });
    console.log(value);
  } else {
    console.log('unknown cmd');
  }
} finally {
  c.close();
}
