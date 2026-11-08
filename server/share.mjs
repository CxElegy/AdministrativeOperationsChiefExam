#!/usr/bin/env node
/**
 * 進度サーバーを、ほかの端末（外出先のスマホなど）からも使えるようにする
 *
 *   npm run share
 *
 * 1. 進度サーバー（server/progress-server.mjs）を動かす
 * 2. cloudflared のトンネルで https のアドレスをもらう（Cloudflare の無料トンネル。アカウント不要）
 * 3. そのアドレス入りの「進度リンク」を表示する。どの端末でもこのリンクで開けば同じ記録になる
 *
 * - 記録はこれまで通りこのパソコンの server/data/ に保存される（トンネルは通り道だけ）
 * - このパソコンの電源を切る・このコマンドを止めると、ほかの端末からはつながらない（ブラウザの中には保存され、次につながったときに合わせる）
 * - 無料トンネルのアドレスは起動するたびに変わる。変わったら、新しく表示されたリンクで開き直す
 * - リンクの ID（u=…）を知っている人は記録を見たり書き換えたりできるので、ほかの人に教えない
 *
 * cloudflared のインストール：
 *   Windows:  winget install --id Cloudflare.cloudflared
 *   Mac:      brew install cloudflared
 *   その他:   https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
 *
 * リンクに入れる ID は SHARE_IDS で変えられる（カンマ区切り）。例：SHARE_IDS=test1-k7m2q9xh4r npm run share
 */
import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.PORT || 8787);
const SITE = process.env.SITE_URL || 'https://cxelegy.github.io/AdministrativeOperationsChiefExam/';
const IDS = (process.env.SHARE_IDS || 'test1-k7m2q9xh4r,test2-p3w8n6zc5t').split(',').map((s) => s.trim()).filter(Boolean);

const server = spawn(process.execPath, [path.join(HERE, 'progress-server.mjs')], { stdio: 'inherit', env: { ...process.env, PORT: String(PORT) } });

const tunnel = spawn('cloudflared', ['tunnel', '--no-autoupdate', '--url', `http://localhost:${PORT}`], { stdio: ['ignore', 'pipe', 'pipe'] });
tunnel.on('error', () => {
	console.error('\ncloudflared が見つかりません。インストールしてからもう一度 npm run share を実行してください。');
	console.error('  Windows:  winget install --id Cloudflare.cloudflared');
	console.error('  Mac:      brew install cloudflared');
	console.error('  その他:   https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/');
	console.error(`\n（同じ Wi-Fi の端末だけなら、トンネルなしで http://<このパソコンのIP>:${PORT}/AdministrativeOperationsChiefExam/?u=<ID> でも開けます）`);
});
let shown = false;
const watch = (buf) => {
	const m = String(buf).match(/https:\/\/[a-z0-9-]+\.trycloudflare\.com/);
	if (!m || shown) return;
	shown = true;
	const api = m[0];
	console.log('\n==================== 進度リンク ====================');
	console.log(`トンネル: ${api}  （このコマンドを動かしている間だけ使えます）\n`);
	for (const id of IDS) console.log(`${id}\n  ${SITE}?u=${encodeURIComponent(id)}&api=${encodeURIComponent(api)}\n`);
	console.log('どの端末でも、同じ ID のリンクで開けば同じ記録になります。');
	console.log('次に起動したときはアドレスが変わるので、そのとき表示されるリンクで開き直してください。');
	console.log('====================================================\n');
};
tunnel.stdout.on('data', watch);
tunnel.stderr.on('data', watch);

const stop = () => { tunnel.kill(); server.kill(); process.exit(0); };
process.on('SIGINT', stop);
process.on('SIGTERM', stop);
server.on('exit', (code) => { tunnel.kill(); process.exit(code ?? 0); });
