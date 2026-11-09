#!/usr/bin/env node
/**
 * 進度サーバー（LocalServer）の今の公開アドレスを、GitHub の tunnel.json に書く
 *
 *   node server/update-tunnel-url.mjs https://xxxx.trycloudflare.com
 *
 * 学習サイトは tunnel.json を読んで進度サーバーのアドレスを知るので、
 * トンネルを起動し直してアドレスが変わっても、リンク（?u=<ID>）は変えなくてよい。
 * トンネルのアドレスが変わるたびに、このスクリプトを呼ぶ（LocalServer の「アドレスが変わったとき」の処理から）。
 *
 * 必要なもの：GITHUB_TOKEN（環境変数、またはこのフォルダか今のフォルダの .env）
 *   GitHub の Fine-grained token で、リポジトリ CxElegy/AdministrativeOperationsChiefExam の
 *   「Contents: Read and write」だけを許可したもの。トークンはほかに書かない・人に教えない。
 * tunnel.json を書き換えても学習サイトの再デプロイは起きない（.github/workflows/deploy.yml で除外している）。
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO = process.env.TUNNEL_REPO || 'CxElegy/AdministrativeOperationsChiefExam';
const BRANCH = process.env.TUNNEL_BRANCH || 'claude/clever-franklin-7sudl7';
const FILE = 'tunnel.json';

function loadEnv(file) {
	try {
		for (const line of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
			const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/);
			if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^['"]|['"]$/g, '');
		}
	} catch { /* .env がなくてもよい */ }
}
loadEnv(path.join(process.cwd(), '.env'));
loadEnv(path.join(path.dirname(fileURLToPath(import.meta.url)), '.env'));

const url = String(process.argv[2] || '').trim().replace(/\/+$/, '');
if (!/^https:\/\/[A-Za-z0-9.-]+(:\d+)?$/.test(url)) { console.error('使い方: node server/update-tunnel-url.mjs https://xxxx.trycloudflare.com'); process.exit(2); }
const token = process.env.GITHUB_TOKEN;
if (!token) { console.error('GITHUB_TOKEN がありません（環境変数か .env に入れてください）'); process.exit(2); }

const api = `https://api.github.com/repos/${REPO}/contents/${FILE}`;
const headers = { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json', 'User-Agent': 'william-room-tunnel-updater', 'X-GitHub-Api-Version': '2022-11-28' };

// 今の tunnel.json（同じアドレスなら書かない。書くときは sha が要る）
let sha;
const cur = await fetch(`${api}?ref=${encodeURIComponent(BRANCH)}`, { headers });
if (cur.ok) {
	const j = await cur.json(); sha = j.sha;
	try { if (JSON.parse(Buffer.from(j.content, 'base64').toString('utf8')).api === url) { console.log('tunnel.json はすでにこのアドレスです:', url); process.exit(0); } } catch { /* 読めなければ書き直す */ }
} else if (cur.status !== 404) { console.error('tunnel.json を読めません:', cur.status, await cur.text()); process.exit(1); }

const body = JSON.stringify({ api: url, updated: new Date().toISOString() }, null, 2) + '\n';
const put = await fetch(api, {
	method: 'PUT', headers,
	body: JSON.stringify({ message: `Update progress server address (${new Date().toISOString()})`, content: Buffer.from(body).toString('base64'), branch: BRANCH, ...(sha ? { sha } : {}) }),
});
if (!put.ok) { console.error('tunnel.json を書けません:', put.status, await put.text()); process.exit(1); }
console.log('tunnel.json を更新しました:', url);
