#!/usr/bin/env node
/**
 * 学習の進度サーバー（自分のパソコンで動かす）
 *
 *   node server/progress-server.mjs            # http://localhost:8787
 *   PORT=9000 node server/progress-server.mjs
 *
 * - 進度は「リンクの ID」ごとに server/data/<ID>.json に保存する（外部ライブラリ不要）
 *   GET  /api/progress/<ID>   → { updated, data }（まだ無ければ 404）
 *   PUT  /api/progress/<ID>   ← { data: { main?, william? } }（キーごとに上書きして保存）
 *   GET  /api/health          → { ok: true }
 * - dist/ があれば、サイトそのものも配信する（同じ Wi-Fi のスマホから http://<パソコンのIP>:8787/ で開ける）
 * - GitHub Pages（https）から使うときは ALLOW_ORIGINS に入っている所からだけ受け付ける
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const DATA_DIR = process.env.DATA_DIR || path.join(HERE, 'data');
const SITE_DIR = process.env.SITE_DIR || path.join(ROOT, 'dist');
const SITE_BASE = (process.env.SITE_BASE || '/AdministrativeOperationsChiefExam').replace(/\/$/, '');
const PORT = Number(process.env.PORT || 8787);
const HOST = process.env.HOST || '0.0.0.0';
const ALLOW_ORIGINS = (process.env.ALLOW_ORIGINS || 'https://cxelegy.github.io,http://localhost:4321,http://127.0.0.1:4321')
	.split(',')
	.map((s) => s.trim())
	.filter(Boolean);
const MAX_BODY = 1024 * 1024; // 1MB
const ID_RE = /^[A-Za-z0-9_-]{12,64}$/;

fs.mkdirSync(DATA_DIR, { recursive: true });

const MIME = {
	'.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
	'.json': 'application/json; charset=utf-8', '.txt': 'text/plain; charset=utf-8', '.svg': 'image/svg+xml',
	'.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.ico': 'image/x-icon', '.woff2': 'font/woff2',
};

function cors(req, res) {
	const origin = req.headers.origin;
	if (origin && (ALLOW_ORIGINS.includes(origin) || ALLOW_ORIGINS.includes('*'))) {
		res.setHeader('Access-Control-Allow-Origin', origin);
		res.setHeader('Vary', 'Origin');
		res.setHeader('Access-Control-Allow-Methods', 'GET, PUT, OPTIONS');
		res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
		// https のページから localhost へ（Chrome の Private Network Access）
		if (req.headers['access-control-request-private-network']) res.setHeader('Access-Control-Allow-Private-Network', 'true');
		res.setHeader('Access-Control-Max-Age', '600');
	}
}

const send = (res, code, obj) => {
	res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' });
	res.end(JSON.stringify(obj));
};

function readBody(req) {
	return new Promise((resolve, reject) => {
		let size = 0;
		const chunks = [];
		req.on('data', (c) => {
			size += c.length;
			if (size > MAX_BODY) { reject(new Error('too large')); req.destroy(); return; }
			chunks.push(c);
		});
		req.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
		req.on('error', reject);
	});
}

const file = (id) => path.join(DATA_DIR, `${id}.json`);
function readRec(id) {
	try { return JSON.parse(fs.readFileSync(file(id), 'utf8')); } catch { return null; }
}
function writeRec(id, rec) {
	const tmp = file(id) + '.tmp';
	fs.writeFileSync(tmp, JSON.stringify(rec));
	fs.renameSync(tmp, file(id));
}

function serveStatic(req, res) {
	let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
	if (p === '/' || p === '') { res.writeHead(302, { Location: SITE_BASE + '/' }); return res.end(); }
	if (!p.startsWith(SITE_BASE + '/') && p !== SITE_BASE) return send(res, 404, { error: 'not found' });
	p = p.slice(SITE_BASE.length) || '/';
	let f = path.normalize(path.join(SITE_DIR, p));
	if (!f.startsWith(SITE_DIR)) return send(res, 403, { error: 'forbidden' });
	if (fs.existsSync(f) && fs.statSync(f).isDirectory()) f = path.join(f, 'index.html');
	if (!fs.existsSync(f)) return send(res, 404, { error: 'not found' });
	res.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream' });
	fs.createReadStream(f).pipe(res);
}

const server = http.createServer(async (req, res) => {
	cors(req, res);
	if (req.method === 'OPTIONS') { res.writeHead(204); return res.end(); }
	const url = new URL(req.url, 'http://x');
	if (url.pathname === '/api/health') return send(res, 200, { ok: true });
	const m = url.pathname.match(/^\/api\/progress\/([^/]+)$/);
	if (m) {
		const id = m[1];
		if (!ID_RE.test(id)) return send(res, 400, { error: 'bad id' });
		if (req.method === 'GET') {
			const rec = readRec(id);
			return rec ? send(res, 200, rec) : send(res, 404, { error: 'not found' });
		}
		if (req.method === 'PUT') {
			try {
				const body = JSON.parse(await readBody(req));
				if (!body || typeof body.data !== 'object' || body.data === null) return send(res, 400, { error: 'bad body' });
				const rec = readRec(id) || { created: Date.now(), data: {} };
				for (const k of ['main', 'william']) if (k in body.data) rec.data[k] = body.data[k];
				rec.updated = Date.now();
				writeRec(id, rec);
				return send(res, 200, { ok: true, updated: rec.updated });
			} catch (e) {
				return send(res, 400, { error: String(e.message || e) });
			}
		}
		return send(res, 405, { error: 'method not allowed' });
	}
	if (req.method === 'GET' && fs.existsSync(SITE_DIR)) return serveStatic(req, res);
	send(res, 404, { error: 'not found' });
});

server.listen(PORT, HOST, () => {
	console.log(`進度サーバー: http://localhost:${PORT}/api/health`);
	console.log(`保存先: ${DATA_DIR}`);
	if (fs.existsSync(SITE_DIR)) console.log(`サイト: http://localhost:${PORT}${SITE_BASE}/`);
	console.log(`受け付けるサイト: ${ALLOW_ORIGINS.join(', ')}`);
});
