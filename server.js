const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const PORT = 3000;
const ROOT = __dirname;

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8'
};

function sendJson(res, statusCode, data) {
  res.writeHead(statusCode, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(data));
}

function serveStaticFile(req, res) {
  const safePath = req.url === '/' ? '/index.html' : req.url;
  const filePath = path.join(ROOT, safePath);

  if (!filePath.startsWith(ROOT)) {
    sendJson(res, 403, { error: 'Forbidden' });
    return;
  }

  fs.readFile(filePath, (err, content) => {
    if (err) {
      sendJson(res, 404, { error: 'File not found' });
      return;
    }

    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': contentType });
    res.end(content);
  });
}

function readRequestBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';

    req.on('data', (chunk) => {
      body += chunk.toString();
    });

    req.on('end', () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch (error) {
        reject(new Error('Invalid JSON body'));
      }
    });

    req.on('error', reject);
  });
}

function runPythonMetrics(source) {
  return new Promise((resolve, reject) => {
    const pythonProcess = spawn('python', ['metrics.py'], { cwd: ROOT });
    let stdout = '';
    let stderr = '';

    pythonProcess.stdout.on('data', (chunk) => {
      stdout += chunk.toString();
    });

    pythonProcess.stderr.on('data', (chunk) => {
      stderr += chunk.toString();
    });

    pythonProcess.on('error', (error) => {
      reject(new Error(`Unable to run Python: ${error.message}`));
    });

    pythonProcess.on('close', (code) => {
      const rawOutput = (stdout || stderr).trim();

      if (!rawOutput) {
        if (code !== 0) {
          reject(new Error(stderr || 'Python process failed'));
        } else {
          reject(new Error('Python returned no output'));
        }
        return;
      }

      try {
        const payload = JSON.parse(rawOutput);

        if (payload && payload.success === false) {
          resolve(payload);
          return;
        }

        if (code !== 0) {
          reject(new Error(payload.error || payload.message || rawOutput));
          return;
        }

        resolve(payload);
      } catch (error) {
        reject(new Error(rawOutput || stderr || 'Python process failed'));
      }
    });

    pythonProcess.stdin.write(source || '');
    pythonProcess.stdin.end();
  });
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);

  if (req.method === 'GET' && (url.pathname === '/' || url.pathname === '/index.html')) {
    serveStaticFile(req, res);
    return;
  }

  if (req.method === 'POST' && url.pathname === '/api/metrics') {
    try {
      const payload = await readRequestBody(req);
      const source = typeof payload.code === 'string' ? payload.code : '';

      if (!source.trim()) {
        sendJson(res, 400, { error: 'Please enter Python code.' });
        return;
      }

      const result = await runPythonMetrics(source);

      if (!result.success) {
        sendJson(res, 400, { error: result.error || 'Invalid Python input.' });
        return;
      }

      sendJson(res, 200, { success: true, results: result.results });
    } catch (error) {
      sendJson(res, 400, { error: error.message || 'Invalid request.' });
    }
    return;
  }

  if (req.method === 'GET' && url.pathname === '/health') {
    sendJson(res, 200, { status: 'ok' });
    return;
  }

  sendJson(res, 404, { error: 'Not found' });
});

server.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
